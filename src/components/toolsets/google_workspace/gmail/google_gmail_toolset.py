import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool

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

    def search_emails_by_date_range(self, start_date: str, end_date: str) -> List[GmailMessage]:
        """
        Searches for emails from the user's inbox within a specified date range.

        Args:
            start_date: The start date in YYYY-MM-DD format.
            end_date: The end date in YYYY-MM-DD format.

        Returns:
            A list of GmailMessage objects.
        """
        self._ensure_service()
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

        logger.info(f"Toolset is calling gmail_service.search_emails with start_date={start_date} and end_date={end_date}")
        return self.gmail_service.search_emails(start_date=start_date_obj, end_date=end_date_obj)

    def get_email(self, message_id: str) -> Optional[GmailMessage]:
        """
        Gets a single email by its ID.
        """
        self._ensure_service()
        return self.gmail_service.get_email(message_id)

    def send_email(self, to: str, subject: str, message_text: str) -> Optional[GmailMessage]:
        """
        Sends an email.
        """
        self._ensure_service()
        return self.gmail_service.send_email(to, subject, message_text)

    def delete_email(self, message_id: str):
        """
        Deletes an email by its ID.
        """
        self._ensure_service()
        self.gmail_service.delete_email(message_id)

    def get_tools(self) -> list[BaseTool]:
        """
        Returns a list of tools provided by this toolset.
        """
        return [
            FunctionTool(func=self.search_emails_by_date_range),
            FunctionTool(func=self.get_email),
            FunctionTool(func=self.send_email),
            FunctionTool(func=self.delete_email),
        ]
