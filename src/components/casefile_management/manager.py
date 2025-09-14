from typing import List, Optional
from src.core.models.casefile import Casefile
from src.core.managers.database_manager import DatabaseManager
from src.core.managers.cache_manager import CacheManager

class CasefileManager:
    """
    Manages the business logic for casefiles, using a database for storage
    and a cache for performance optimization.
    """
    def __init__(self, db_manager: DatabaseManager, cache_manager: CacheManager):
        self.db_manager = db_manager
        self.cache_manager = cache_manager

    async def create_casefile(self, name: str, owner_id: str) -> Casefile:
        """Creates a new casefile, saves it to the database, and returns it."""
        new_casefile = Casefile(name=name, owner_id=owner_id)
        
        # Sla het op in de database via de DatabaseManager
        await self.db_manager.save(
            collection="casefiles",
            doc_id=new_casefile.id,
            data=new_casefile.model_dump(mode="json")
        )
        return new_casefile

    async def get_casefile(self, casefile_id: str) -> Optional[Casefile]:
        """
        Retrieves a casefile, first checking the cache and then falling back
        to the database.
        """
        cache_key = f"casefile:{casefile_id}"
        
        # 1. Probeer de cache
        cached_data = self.cache_manager.get(cache_key)
        if cached_data:
            return Casefile(**cached_data)

        # 2. Als niet in cache, haal uit de database
        casefile_data = await self.db_manager.get("casefiles", casefile_id)
        if casefile_data:
            casefile = Casefile(**casefile_data)
            # 3. Sla het resultaat op in de cache voor de volgende keer
            self.cache_manager.set(cache_key, casefile.model_dump(mode="json"))
            return casefile
            
        return None

    async def list_casefiles(self) -> List[Casefile]:
        """Lists all casefiles from the database."""
        all_casefiles_data = await self.db_manager.get_all("casefiles")
        return [Casefile(**data) for data in all_casefiles_data]