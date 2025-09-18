import inspect
from typing import List, Dict, Any

from MDSAPP.toolsets.casefile_toolset import CasefileToolset
from MDSAPP.toolsets.GoogleWorkspace.google_drive_toolset import GoogleDriveToolset
from MDSAPP.toolsets.GoogleWorkspace.google_gmail_toolset import GoogleGmailToolset
from MDSAPP.toolsets.GoogleWorkspace.google_docs_toolset import GoogleDocsToolset
from MDSAPP.toolsets.GoogleWorkspace.google_sheets_toolset import GoogleSheetsToolset
from MDSAPP.toolsets.GoogleWorkspace.google_calendar_toolset import GoogleCalendarToolset
from MDSAPP.toolsets.GoogleWorkspace.google_people_toolset import GooglePeopleToolset
from MDSAPP.toolsets.retrieval_toolset import RetrievalToolset
from MDSAPP.toolsets.web_search_toolset import WebSearchToolset


class SystemCapabilitiesService:
    """
    Provides an overview of the system's capabilities, including tools, agents, and flows.
    """
    def __init__(self, 
                 casefile_toolset: CasefileToolset,
                 drive_toolset: GoogleDriveToolset,
                 gmail_toolset: GoogleGmailToolset,
                 docs_toolset: GoogleDocsToolset,
                 sheets_toolset: GoogleSheetsToolset,
                 calendar_toolset: GoogleCalendarToolset,
                 people_toolset: GooglePeopleToolset,
                 retrieval_toolset: RetrievalToolset,
                 web_search_toolset: WebSearchToolset):
        self._tools = []
        self._tools.extend(casefile_toolset.get_tools())
        self._tools.extend(drive_toolset.get_tools())
        self._tools.extend(gmail_toolset.get_tools())
        self._tools.extend(docs_toolset.get_tools())
        self._tools.extend(sheets_toolset.get_tools())
        self._tools.extend(calendar_toolset.get_tools())
        self._tools.extend(people_toolset.get_tools())
        self._tools.extend(retrieval_toolset.get_tools())
        self._tools.extend(web_search_toolset.get_tools())

    def get_all_capabilities(self) -> Dict[str, Any]:
        """
        Returns a dictionary containing all the system's capabilities.
        """
        return {
            "atomic_tools": self.get_atomic_tools(),
            "agent_tools": self.get_agent_tools(),
        }

    def get_atomic_tools(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all registered atomic tools.
        """
        atomic_tools = []
        for tool in self._tools:
            # The tool object is now a FunctionTool, so we access the function via .func
            func = tool.func
            atomic_tools.append({
                "name": func.__name__,
                "description": inspect.getdoc(func),
            })
        return atomic_tools

    def get_agent_tools(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all registered agent tools.
        """
        return []