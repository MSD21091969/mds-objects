import logging
import base64
import asyncio
from email.mime.text import MIMEText
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple

from googleapiclient.errors import HttpError

from src.components.toolsets.google_workspace.base_service import BaseGoogleService
from .models import GmailMessage, Attachment

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.modify'] # Modify scope for full CRUD
SERVICE_NAME = 'gmail'
SERVICE_VERSION = 'v1'

class GoogleGmailService(BaseGoogleService):
    """
    A service class to interact with the Google Gmail API, inheriting common logic
    from BaseGoogleService.
    """
    def __init__(self, client_secrets_path: str, token_path: str = "token.json", port: int = 8080):
        super().__init__(client_secrets_path, token_path, port=port)
        self._build_service(SERVICE_NAME, SERVICE_VERSION, SCOPES)

    def _parse_message_payload(self, payload: Dict[str, Any]) -> Tuple[Optional[str], List[Attachment]]:
        """Recursively parses a message payload to find the body and attachments."""
        body = None
        attachments = []
        mime_type = payload.get('mimeType', '')

        if 'parts' in payload:
            for part in payload['parts']:
                part_body, part_attachments = self._parse_message_payload(part)
                if not body and part_body: # Take the first body part found
                    body = part_body
                attachments.extend(part_attachments)
        elif mime_type.startswith('text/'):
            data = payload.get('body', {}).get('data')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        # Check for attachments at the current level
        if payload.get('filename') and payload.get('body', {}).get('attachmentId'):
            try:
                attachment = Attachment(
                    attachmentId=payload['body']['attachmentId'],
                    filename=payload['filename'],
                    mimeType=payload.get('mimeType', 'application/octet-stream'),
                    size=payload.get('body', {}).get('size', 0)
                )
                attachments.append(attachment)
            except Exception as e:
                logger.warning(f"Could not parse an attachment: {e}")

        return body, attachments

    async def search_emails(self, start_date: date, end_date: date) -> List[GmailMessage]:
        """
        Searches for emails within a specific date range and retrieves their full content.
        """
        if not self.service:
            logger.error("GoogleGmailService is not authenticated. Cannot search emails.")
            return []

        try:
            inclusive_start_date = start_date - timedelta(days=1)
            query = f"after:{inclusive_start_date.strftime('%Y/%m/%d')} before:{end_date.strftime('%Y/%m/%d')}"
            logger.info(f"Searching Gmail with query: '{query}'")
            
            response = await asyncio.to_thread(
                self.service.users().messages().list(userId='me', q=query).execute
            )
            messages = response.get('messages', [])

            if not messages:
                logger.info("No emails found for the specified date range.")
                return []

            email_list = []
            for msg in messages:
                msg_data = await asyncio.to_thread(
                    self.service.users().messages().get(userId='me', id=msg['id'], format='full').execute
                )
                
                headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
                body, attachments = self._parse_message_payload(msg_data.get('payload', {}))
                
                email_details = {
                    "id": msg_data['id'],
                    "threadId": msg_data['threadId'],
                    "snippet": msg_data['snippet'],
                    "headers": headers,
                    "body": body,
                    "attachments": attachments,
                    "internalDate": msg_data.get('internalDate')
                }
                email_list.append(GmailMessage(**email_details))
            
            logger.info(f"Found and processed {len(email_list)} emails.")
            return email_list

        except HttpError as error:
            logger.error(f"An error occurred while searching emails: {error}")
            return []

    async def get_attachment(self, message_id: str, attachment_id: str) -> Optional[bytes]:
        """Gets the raw data of a specific attachment."""
        if not self.service:
            logger.error("GoogleGmailService is not authenticated. Cannot get attachment.")
            return None
        try:
            attachment_data = self.service.users().messages().attachments().get(
                userId='me', messageId=message_id, id=attachment_id
            )
            attachment_data = await asyncio.to_thread(attachment_data.execute)
            file_data = base64.urlsafe_b64decode(attachment_data['data'].encode('UTF-8'))
            return file_data
        except HttpError as error:
            logger.error(f"An error occurred while getting attachment {attachment_id}: {error}")
            return None

    async def get_email(self, message_id: str) -> Optional[GmailMessage]:
        """
        Gets a single email by its ID.
        """
        if not self.service:
            logger.error("GoogleGmailService is not authenticated. Cannot get email.")
            return None
        try:
            msg_data = await asyncio.to_thread(
                self.service.users().messages().get(userId='me', id=message_id, format='full').execute
            )
            headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
            body, attachments = self._parse_message_payload(msg_data.get('payload', {}))
            email_details = {
                "id": msg_data['id'],
                "threadId": msg_data['threadId'],
                "snippet": msg_data['snippet'],
                "headers": headers,
                "body": body,
                "attachments": attachments,
                "internalDate": msg_data.get('internalDate')
            }
            return GmailMessage(**email_details)
        except HttpError as error:
            logger.error(f"An error occurred while getting email {message_id}: {error}")
            return None

    async def send_email(self, to: str, subject: str, message_text: str) -> Optional[GmailMessage]:
        """
        Sends an email.
        """
        if not self.service:
            logger.error("GoogleGmailService is not authenticated. Cannot send email.")
            return None
        try:
            message = MIMEText(message_text)
            message['to'] = to
            message['subject'] = subject
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            body = {'raw': raw_message}
            sent_message = await asyncio.to_thread(
                self.service.users().messages().send(userId='me', body=body).execute
            )
            return await self.get_email(sent_message['id'])
        except HttpError as error:
            logger.error(f"An error occurred while sending email: {error}")
            return None

    async def delete_email(self, message_id: str):
        """
        Deletes an email by its ID.
        """
        if not self.service:
            logger.error("GoogleGmailService is not authenticated. Cannot delete email.")
            return
        try:
            await asyncio.to_thread(
                self.service.users().messages().delete(userId='me', id=message_id).execute
            )
            logger.info(f"Email with ID '{message_id}' deleted successfully.")
        except HttpError as error:
            logger.error(f"An error occurred while deleting email {message_id}: {error}")