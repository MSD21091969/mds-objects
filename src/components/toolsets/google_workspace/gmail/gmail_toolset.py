import logging
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.genai import types as adk_types
from datetime import date

from src.components.toolsets.google_workspace.gmail.service import GoogleGmailService
from src.components.toolsets.google_workspace.gmail.models import GmailMessage

logger = logging.getLogger(__name__)

class GmailToolset(BaseToolset):
    """A toolset for interacting with Gmail."""

    def __init__(self, client_secrets_path: str, token_path: str):
        self.gmail_service = GoogleGmailService(client_secrets_path, token_path)
        super().__init__()

    def _search_emails(self, start_date: str, end_date: str) -> str:
        """Searches for emails within a specific date range (YYYY-MM-DD) and retrieves their full content."""
        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
            emails = self.gmail_service.search_emails(start, end)
            return "\n".join([email.json() for email in emails])
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return f"Error searching emails: {e}"

    def _get_email(self, message_id: str) -> str:
        """Gets a single email by its ID."""
        try:
            email = self.gmail_service.get_email(message_id)
            return email.json() if email else "Email not found."
        except Exception as e:
            logger.error(f"Error getting email: {e}")
            return f"Error getting email: {e}"

    def _send_email(self, to: str, subject: str, message_text: str) -> str:
        """Sends an email."""
        try:
            sent_email = self.gmail_service.send_email(to, subject, message_text)
            return sent_email.json() if sent_email else "Failed to send email."
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return f"Error sending email: {e}"

    def get_tools(self) -> list[BaseTool]:
        """Returns a list of all the tool methods in this toolset."""
        search_emails_declaration = adk_types.FunctionDeclaration(
            name="search_emails",
            description="Searches for emails within a specific date range (YYYY-MM-DD) and retrieves their full content.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "start_date": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The start date for the search in YYYY-MM-DD format.",
                    ),
                    "end_date": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The end date for the search in YYYY-MM-DD format.",
                    ),
                },
                required=["start_date", "end_date"],
            ),
            returns=adk_types.Schema(
                type=adk_types.SchemaType.STRING,
                description="A JSON string containing a list of matching emails.",
            ),
        )

        get_email_declaration = adk_types.FunctionDeclaration(
            name="get_email",
            description="Gets a single email by its ID.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "message_id": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The ID of the email message.",
                    ),
                },
                required=["message_id"],
            ),
            returns=adk_types.Schema(
                type=adk_types.SchemaType.STRING,
                description="A JSON string containing the email details, or 'Email not found.'.",
            ),
        )

        send_email_declaration = adk_types.FunctionDeclaration(
            name="send_email",
            description="Sends an email.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "to": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The recipient's email address.",
                    ),
                    "subject": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The subject of the email.",
                    ),
                    "message_text": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The body of the email.",
                    ),
                },
                required=["to", "subject", "message_text"],
            ),
            returns=adk_types.Schema(
                type=adk_types.SchemaType.STRING,
                description="A JSON string containing the sent email details, or 'Failed to send email.'.",
            ),
        )

        return [
            FunctionTool(
                func=self._search_emails,
                declaration=search_emails_declaration,
            ),
            FunctionTool(
                func=self._get_email,
                declaration=get_email_declaration,
            ),
            FunctionTool(
                func=self._send_email,
                declaration=send_email_declaration,
            ),
        ]
