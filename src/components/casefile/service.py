# src/components/casefile/service.py

import logging
from typing import Dict, Any, List, Optional
from uuid import uuid4
import datetime
import asyncio
import json
from firebase_admin import firestore

from .models import Casefile, ProcessedArtifact
from src.core.models.user import User
from src.core.models.ontology import CasefileRole
from src.core.models.user import UserRole

logger = logging.getLogger(__name__)

class CasefileService:
    """
    Manages the business logic for the lifecycle of hierarchical casefiles.
    """
    def __init__(self, db_manager, cache_manager):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        logger.info("CasefileService initialized.")

    async def create_casefile(
        self,
        user_id: str,
        name: str,
        description: str,
        parent_id: Optional[str] = None,
        casefile_id: Optional[str] = None,
    ) -> Casefile:
        """
        Creates a new casefile, optionally as a sub-casefile of an existing one.
        Returns the newly created Casefile object.
        """
        current_user = await self.db_manager.get_user_by_username(user_id)
        if not current_user:
            raise ValueError(f"User with ID '{user_id}' not found.")
        if parent_id:
            # Use a Firestore transaction to ensure atomicity
            transaction = self.db_manager.db.transaction()

            @firestore.transactional
            def _create_sub_casefile_in_transaction(transaction):
                parent_ref = self.db_manager.db.collection(self.db_manager.casefiles_collection_name).document(parent_id)
                parent_doc = parent_ref.get(transaction=transaction)

                if not parent_doc.exists:
                    raise ValueError(f"Parent casefile with ID '{parent_id}' not found.")

                parent_casefile = Casefile(**parent_doc.to_dict())

                # Permission Check: User must be a System Admin OR have write access to the parent
                user_role_in_acl = parent_casefile.acl.get(user_id)
                if not (current_user.role == UserRole.ADMIN or user_role_in_acl in [CasefileRole.ADMIN, CasefileRole.WRITER]):
                     raise PermissionError(f"User '{user_id}' does not have permission to create a sub-casefile under '{parent_id}'.")

                # Inherit ACL and add creator as admin
                sub_acl = parent_casefile.acl.copy()
                sub_acl[user_id] = CasefileRole.ADMIN

                sub_casefile = Casefile(
                    name=name,
                    description=description,
                    owner_id=user_id,
                    acl=sub_acl,
                    created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    modified_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
                )

                # Add sub-casefile ID to parent
                parent_casefile.sub_casefile_ids.append(sub_casefile.id)
                parent_casefile.touch()

                # Stage the writes in the transaction
                sub_ref = self.db_manager.db.collection(self.db_manager.casefiles_collection_name).document(sub_casefile.id)
                transaction.set(sub_ref, sub_casefile.model_dump(exclude_none=True))
                transaction.set(parent_ref, parent_casefile.model_dump(exclude_none=True))

                return sub_casefile

            # Run the transactional function in a separate thread
            sub_casefile = await asyncio.to_thread(_create_sub_casefile_in_transaction, transaction)
            logger.info(f"Sub-casefile '{sub_casefile.id}' created and saved under parent '{parent_id}' in a transaction.")
            return sub_casefile
        else:
            # If casefile_id is provided, use it. Otherwise, the Casefile model's default_factory will generate it.
            casefile_data = {
                "name": name,
                "description": description,
                "owner_id": user_id,
                "acl": {user_id: CasefileRole.ADMIN},
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "modified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            if casefile_id:
                casefile_data["id"] = casefile_id
            
            casefile = Casefile(**casefile_data)
            
            await self.db_manager.save_casefile(casefile)
            logger.info(f"Top-level casefile '{casefile.id}' created by user '{user_id}'.")
            return casefile

    async def list_all_casefiles(self) -> List[Casefile]: # The return hint is correct
        """Lists all casefiles from the database."""
        # The error occurs because get_all returns a list of dicts, not Casefile objects.
        # We need to convert each dictionary into a Casefile model instance.
        casefile_dicts = await self.db_manager.get_all("casefiles")
        return [Casefile(**cf_dict) for cf_dict in casefile_dicts]

    async def list_top_level_casefiles(self) -> List[Casefile]:
        """Retrieves all casefiles and filters for only top-level ones."""
        all_casefiles = await self.list_all_casefiles()
        return [casefile for casefile in all_casefiles if getattr(casefile, 'parent_id', None) is None]

    async def list_all_casefiles_with_status(self) -> List[Dict[str, Any]]:
        """Lists all casefiles and adds a dummy status."""
        all_casefiles = await self.list_all_casefiles()
        casefiles_with_status = []
        for casefile in all_casefiles:
            cf_dict = casefile.model_dump()
            cf_dict["status"] = "active"  # Add dummy status
            casefiles_with_status.append(cf_dict)
        return casefiles_with_status

    async def delete_casefile(self, casefile_id: str, user_id: str) -> bool:
        """Deletes a casefile from the database."""
        current_user = await self.db_manager.get_user_by_username(user_id)
        if not current_user:
            raise ValueError(f"User with ID '{user_id}' not found.")
        
        casefile = await self.load_casefile(casefile_id)
        if not casefile:
            raise ValueError(f"Casefile with ID '{casefile_id}' not found.")

        # Permission Check: User must be a System Admin OR a Casefile Admin
        if not (current_user.role == UserRole.ADMIN or casefile.acl.get(current_user.username) == CasefileRole.ADMIN):
            raise PermissionError(f"User '{current_user.username}' does not have admin rights to delete casefile '{casefile_id}'.")

        logger.info(f"Casefile '{casefile_id}' deleted by user '{current_user.username}'.")
        return await self.db_manager.delete_casefile(casefile_id)

    async def load_casefile(self, casefile_id: str) -> Optional[Casefile]:
        """
        Loads a casefile object, using the cache first.
        """
        cache_key = f"casefile:{casefile_id}"
        
        # 1. Try to get from cache
        cached_casefile_data = self.cache_manager.get(cache_key)
        if cached_casefile_data:
            logger.debug(f"Cache HIT for {cache_key}")
            return Casefile(**cached_casefile_data)

        # 2. If miss, get from DB
        logger.debug(f"Cache MISS for {cache_key}. Loading from DB.")
        casefile = await self.db_manager.load_casefile(casefile_id)

        if casefile:
            # 3. Store in cache before returning
            casefile_data = casefile.model_dump(exclude_none=True)
            self.cache_manager.set(cache_key, casefile_data)
            return casefile
            
        return None

    async def update_casefile(self, casefile_id: str, updates: Dict[str, Any], user_id: str) -> Casefile:
        current_user = await self.db_manager.get_user_by_username(user_id)
        if not current_user:
            raise ValueError(f"User with ID '{user_id}' not found.")

        # First, ensure the casefile exists using the cached loader.
        # This warms the cache and provides a clear failure point before the transaction.
        casefile_to_update = await self.load_casefile(casefile_id)
        if not casefile_to_update:
            raise ValueError(f"Casefile with ID '{casefile_id}' not found.")
        """
        Updates an existing casefile with the provided data within a transaction.
        Handles appending to lists and updating other fields atomically.
        """
        transaction = self.db_manager.db.transaction()

        @firestore.transactional
        def _update_in_transaction(transaction, casefile_id, current_user, updates):
            casefile_ref = self.db_manager.db.collection(self.db_manager.casefiles_collection_name).document(casefile_id)
            casefile_snapshot = casefile_ref.get(transaction=transaction)

            if not casefile_snapshot.exists:
                raise ValueError(f"Casefile with ID '{casefile_id}' not found.")

            casefile = Casefile(**casefile_snapshot.to_dict())

            # Permission Check: User must be a System Admin OR have write permission in the ACL
            user_role_in_acl = casefile.acl.get(current_user.username)
            if not (current_user.role == UserRole.ADMIN or user_role_in_acl in [CasefileRole.ADMIN, CasefileRole.WRITER]):
                raise PermissionError(f"User '{current_user.username}' does not have write permission for casefile '{casefile_id}'.")

            for key, value in updates.items():
                if hasattr(casefile, key):
                    current_field_value = getattr(casefile, key)
                    # Check if the field is a list and the update value is also a list
                    if isinstance(current_field_value, list) and isinstance(value, list):
                        # This logic handles appending complex objects (like DriveFile)
                        # and preventing duplicates based on their 'id' or 'object_id'.
                        
                        # Create a dictionary of existing items by their ID for quick lookups.
                        # It assumes items in the list are Pydantic models with an 'id' or similar unique field.
                        # We handle both dicts (from model_dump) and model objects.
                        existing_items_map = {}
                        for item in current_field_value:
                            if isinstance(item, dict):
                                item_id = item.get('id') or item.get('object_id')
                                if item_id: existing_items_map[item_id] = item
                            elif hasattr(item, 'id'):
                                existing_items_map[item.id] = item

                        # Add new items if they are not already in the map.
                        for new_item_data in value:
                            new_item_id = new_item_data.get('id') or new_item_data.get('object_id')
                            if new_item_id and new_item_id not in existing_items_map:
                                existing_items_map[new_item_id] = new_item_data
                        
                        # Set the attribute to the new list of unique items.
                        setattr(casefile, key, list(existing_items_map.values()))
                    else:
                        # Handling for simple, non-list fields (name, description, etc.)
                        setattr(casefile, key, value)
                else:
                    logger.warning(f"Attempted to update non-existent attribute '{key}' on Casefile '{casefile_id}'.")

            casefile.touch()  # Update modified_at timestamp

            # Stage the write in the transaction
            transaction.set(casefile_ref, casefile.model_dump(exclude_none=True))
            
            return casefile

        # Run the synchronous transactional function in a separate thread to avoid blocking the event loop
        updated_casefile = await asyncio.to_thread(
            _update_in_transaction, transaction, casefile_id, current_user, updates
        )
        
        logger.info(f"Casefile '{updated_casefile.id}' updated successfully by user '{current_user.username}' in a transaction.")
        return updated_casefile

    async def add_document_to_subcollection(self, casefile_id: str, subcollection_name: str, document_data: dict, document_id: str = None):
        """
        Adds a document to a subcollection of a casefile.
        """
        casefile_ref = self.db_manager.db.collection("casefiles").document(casefile_id)
        subcollection_ref = casefile_ref.collection(subcollection_name)
        if document_id:
            doc_ref = subcollection_ref.document(document_id)
        else:
            doc_ref = subcollection_ref.document()
        
        await asyncio.to_thread(doc_ref.set, document_data)
        logger.info(f"Added document to subcollection '{subcollection_name}' in casefile '{casefile_id}'.")

    async def grant_access(self, casefile_id: str, user_id_to_grant: str, role: str, current_user_id: str) -> Casefile:
        """
        Grants a user a specific role on a casefile's ACL within a transaction.
        """
        try:
            validated_role = CasefileRole(role.lower())
        except ValueError:
            raise ValueError(f"Invalid role '{role}'. Must be one of {[r.value for r in CasefileRole]}.")

        current_user = await self.db_manager.get_user_by_username(current_user_id)
        if not current_user:
            raise ValueError(f"User with ID '{current_user_id}' not found.")

        user_to_grant = await self.db_manager.get_user_by_username(user_id_to_grant)
        if not user_to_grant:
            raise ValueError(f"User to grant access to with ID '{user_id_to_grant}' not found.")

        transaction = self.db_manager.db.transaction()

        @firestore.transactional
        def _grant_in_transaction(transaction, casefile_id, current_user, user_id_to_grant, role_to_grant):
            casefile_ref = self.db_manager.db.collection(self.db_manager.casefiles_collection_name).document(casefile_id)
            casefile_snapshot = casefile_ref.get(transaction=transaction)

            if not casefile_snapshot.exists:
                raise ValueError(f"Casefile with ID '{casefile_id}' not found.")

            casefile = Casefile(**casefile_snapshot.to_dict())

            # Permission Check: Current user must be a System Admin OR a Casefile Admin
            if not (current_user.role == UserRole.ADMIN or casefile.acl.get(current_user.username) == CasefileRole.ADMIN):
                raise PermissionError(f"User '{current_user.username}' does not have admin rights to grant access to casefile '{casefile_id}'.")

            casefile.acl[user_id_to_grant] = role_to_grant
            casefile.touch()

            transaction.set(casefile_ref, casefile.model_dump(exclude_none=True))
            return casefile

        updated_casefile = await asyncio.to_thread(
            _grant_in_transaction, transaction, casefile_id, current_user, user_id_to_grant, validated_role
        )

        logger.info(f"Access to casefile '{updated_casefile.id}' granted to user '{user_id_to_grant}' with role '{validated_role.value}' by user '{current_user.username}'.")
        return updated_casefile

    async def revoke_access(self, casefile_id: str, user_id_to_revoke: str, current_user_id: str) -> Casefile:
        """
        Revokes a user's access from a casefile's ACL within a transaction.
        """
        current_user = await self.db_manager.get_user_by_username(current_user_id)
        if not current_user:
            raise ValueError(f"User with ID '{current_user_id}' not found.")

        transaction = self.db_manager.db.transaction()

        @firestore.transactional
        def _revoke_in_transaction(transaction, casefile_id, current_user, user_id_to_revoke):
            casefile_ref = self.db_manager.db.collection(self.db_manager.casefiles_collection_name).document(casefile_id)
            casefile_snapshot = casefile_ref.get(transaction=transaction)

            if not casefile_snapshot.exists:
                raise ValueError(f"Casefile with ID '{casefile_id}' not found.")

            casefile = Casefile(**casefile_snapshot.to_dict())

            # Permission Check: Current user must be a System Admin OR a Casefile Admin
            if not (current_user.role == UserRole.ADMIN or casefile.acl.get(current_user.username) == CasefileRole.ADMIN):
                raise PermissionError(f"User '{current_user.username}' does not have admin rights to revoke access from casefile '{casefile_id}'.")

            if user_id_to_revoke not in casefile.acl:
                raise ValueError(f"User '{user_id_to_revoke}' does not have access to casefile '{casefile_id}' to begin with.")

            # Prevent owner from having their access revoked by anyone other than themselves (as a safety measure)
            if casefile.owner_id == user_id_to_revoke and current_user.username != user_id_to_revoke:
                 raise PermissionError("The casefile owner's access cannot be revoked by another user.")

            del casefile.acl[user_id_to_revoke]
            casefile.touch()

            transaction.set(casefile_ref, casefile.model_dump(exclude_none=True))
            return casefile

        updated_casefile = await asyncio.to_thread(
            _revoke_in_transaction, transaction, casefile_id, current_user, user_id_to_revoke
        )

        logger.info(f"Access to casefile '{updated_casefile.id}' revoked for user '{user_id_to_revoke}' by user '{current_user.username}'.")
        return updated_casefile

    async def link_session_to_casefile(self, casefile_id: str, session_id: str) -> None:
        """
        Links an ADK session ID to a casefile by appending it to the
        session_ids list. This is done in a transaction to ensure atomicity.
        """
        casefile_ref = self.db_manager.db.collection(self.db_manager.casefiles_collection_name).document(casefile_id)

        @firestore.transactional
        def _link_in_transaction(transaction, case_ref, sess_id):
            snapshot = case_ref.get(transaction=transaction)
            if not snapshot.exists:
                logger.warning(f"Cannot link session. Casefile '{casefile_id}' not found.")
                return

            # Using Firestore's ArrayUnion to atomically add the new session ID
            # if it's not already present.
            transaction.update(case_ref, {
                "session_ids": firestore.ArrayUnion([sess_id])
            })

        transaction = self.db_manager.db.transaction()
        await asyncio.to_thread(_link_in_transaction, transaction, casefile_ref, session_id)
        logger.info(f"Successfully linked session '{session_id}' to casefile '{casefile_id}'.")

    async def get_active_directives(self) -> list[dict]:
        """
        (Placeholder for future development)
        Retrierieves all currently active SystemDirectives from Firestore.
        """
        logger.info("Future feature: Checking for active system directives...")
        # In the future, this would query the 'system_directives' collection group
        # where 'is_active' == True.
        return []

    async def add_to_list_field(self, casefile_id: str, field_name: str, value_to_add: Any, user_id: str) -> Optional[Casefile]:
        """
        Adds a value to a list field within a casefile document if it's not already present.
        This is a convenience method that uses the main update_casefile logic.
        """
        casefile = await self.load_casefile(casefile_id)
        if not casefile:
            logger.error(f"Cannot add to list, casefile {casefile_id} not found.")
            return None

        # The update_casefile method already performs authorization checks.

        current_list = getattr(casefile, field_name, [])
        if not isinstance(current_list, list):
             logger.error(f"Field '{field_name}' on casefile '{casefile_id}' is not a list.")
             return None # Or raise an error

        if value_to_add not in current_list:
            # We create a new list to ensure the change is detected.
            updated_list = current_list + [value_to_add]
            updates = {field_name: updated_list}
            # Call the main update method which handles transactions and caching
            return await self.update_casefile(casefile_id, updates, user_id)

        # If the value is already in the list, no update is needed.
        logger.debug(f"Value '{value_to_add}' already exists in field '{field_name}' for casefile '{casefile_id}'. No update performed.")
        return casefile