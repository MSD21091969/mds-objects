import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools import ToolContext
from google.genai import types as adk_types

from src.components.toolsets.google_workspace.gmail.service import GoogleGmailService
from src.components.toolsets.google_workspace.gmail.models import GmailMessage

logger = logging.getLogger(__name__)

class GoogleGmailToolset(BaseToolset):
    """
    A toolset for interacting with Google Gmail.
    """
    def __init__(self, gmail_service: Optional[GoogleGmailService]):
        super().__init__()
        self.gmail_service = gmail_service

    def _ensure_service(self):
        """Checks if the Gmail service is available."""
        if not self.gmail_service or not self.gmail_service.service:
            raise ConnectionError("GoogleGmailService is not available or not authenticated.")

    def _search_emails_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Searches for emails from the user's inbox within a specified date range.

        Args:
            start_date: The start date in YYYY-MM-DD format.
            end_date: The end date in YYYY-MM-DD format.

        Returns:
            A list of dictionaries representing GmailMessage objects.
        """
        self._ensure_service()
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

        logger.info(f"Toolset is calling gmail_service.search_emails with start_date={start_date} and end_date={end_date}")
        messages = self.gmail_service.search_emails(start_date=start_date_obj, end_date=end_date_obj)
        return [msg.model_dump() for msg in messages]

    def _get_email(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets a single email by its ID.
        """
        self._ensure_service()
        email = self.gmail_service.get_email(message_id)
        return email.model_dump() if email else None

    def _send_email(self, to: str, subject: str, message_text: str) -> Optional[Dict[str, Any]]:
        """
        Sends an email.
        """
        self._ensure_service()
        sent_email = self.gmail_service.send_email(to, subject, message_text)
        return sent_email.model_dump() if sent_email else None

    def _delete_email(self, message_id: str) -> str:
        """
        Deletes an email by its ID.
        """
        self._ensure_service()
        self.gmail_service.delete_email(message_id)
        return f"Email with ID '{message_id}' deleted successfully."

    def get_tools(self, tool_context: "ToolContext") -> list[BaseTool]:
        """
        Returns a list of tools provided by this toolset.
        """
        gmail_attachment_schema = {
            "type": adk_types.Type.OBJECT,
            "properties": {
                'attachment_id': {"type": adk_types.Type.STRING, "description": "The attachment's ID."},
                'filename': {"type": adk_types.Type.STRING, "description": "The original filename of the attachment."},
                'mime_type': {"type": adk_types.Type.STRING, "description": "The MIME type of the attachment."},
                'size': {"type": adk_types.Type.INTEGER, "description": "The size of the attachment in bytes."},
            }
        }

        gmail_message_schema = {
            "type": adk_types.Type.OBJECT,
            "description": "Represents a single Gmail email message.",
            "properties": {
                'id': {"type": adk_types.Type.STRING, "description": "The unique ID of the email message."},
                'thread_id': {"type": adk_types.Type.STRING, "description": "The ID of the thread the message belongs to."},
                'subject': {"type": adk_types.Type.STRING, "description": "The subject line of the email."},
                'from_address': {"type": adk_types.Type.STRING, "description": "The sender's email address."},
                'to_addresses': {"type": adk_types.Type.ARRAY, "items": {"type": adk_types.Type.STRING}, "description": "List of recipient email addresses."},
                'date': {"type": adk_types.Type.STRING, "description": "The date the email was sent, in ISO 8601 format."},
                'snippet': {"type": adk_types.Type.STRING, "description": "A short snippet of the email's content."},
                'body_plain': {"type": adk_types.Type.STRING, "description": "The plain text body of the email."},
                'body_html': {"type": adk_types.Type.STRING, "description": "The HTML body of the email."},
                'attachments': {"type": adk_types.Type.ARRAY, "items": gmail_attachment_schema, "description": "A list of attachments in the email."},
            }
        }

        search_emails_declaration = adk_types.FunctionDeclaration(
            name="search_gmail_emails",
            description="Searches for emails in the user's inbox within a specified date range.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'start_date': {"type": adk_types.Type.STRING, "description": "The start date for the search in YYYY-MM-DD format."},
                    'end_date': {"type": adk_types.Type.STRING, "description": "The end date for the search in YYYY-MM-DD format."},
                },
                required=['start_date', 'end_date']
            ),
            returns=adk_types.FunctionDeclaration.schema(**{
                "type": adk_types.Type.ARRAY,
                "items": gmail_message_schema
            })
        )

        get_email_declaration = adk_types.FunctionDeclaration(
            name="get_gmail_email",
            description="Retrieves the full details of a single email by its message ID.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'message_id': {"type": adk_types.Type.STRING, "description": "The unique ID of the email message to retrieve."},
                },
                required=['message_id']
            ),
            returns=adk_types.FunctionDeclaration.schema(**gmail_message_schema)
        )

        send_email_declaration = adk_types.FunctionDeclaration(
            name="send_gmail_email",
            description="Creates and sends a new email message.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'to': {"type": adk_types.Type.STRING, "description": "The recipient's email address."},
                    'subject': {"type": adk_types.Type.STRING, "description": "The subject line of the email."},
                    'message_text': {"type": adk_types.Type.STRING, "description": "The plain text body of the email."}
                },
                required=['to', 'subject', 'message_text']
            ),
            returns=adk_types.FunctionDeclaration.schema(**gmail_message_schema)
        )

        delete_email_declaration = adk_types.FunctionDeclaration(
            name="delete_gmail_email",
            description="Permanently deletes an email by its message ID. This action cannot be undone.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    'message_id': {"type": adk_types.Type.STRING, "description": "The unique ID of the email message to delete."},
                },
                required=['message_id']
            ),
            returns=adk_types.FunctionDeclaration.schema(**{"type": adk_types.Type.STRING, "description": "A confirmation message indicating success."})
        )

        return [
            FunctionTool(
                func=self._search_emails_by_date_range,
                declaration=search_emails_declaration
            ),
            FunctionTool(
                func=self._get_email,
                declaration=get_email_declaration
            ),
            FunctionTool(
                func=self._send_email,
                declaration=send_email_declaration
            ),
            FunctionTool(
                func=self._delete_email,
                declaration=delete_email_declaration
            ),
        ]
