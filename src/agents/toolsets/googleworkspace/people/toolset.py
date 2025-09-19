# src/components/toolsets/google_workspace/people/google_people_toolset.py

import logging
from typing import Optional

from google.adk.tools import FunctionTool, BaseToolset, ToolContext, ReadonlyContext
from google.adk.tools.base_tool import BaseTool

from .service import PeopleService
from .models import SearchContactsQuery

logger = logging.getLogger(__name__)

class PeopleToolset(BaseToolset):
    def __init__(self, people_service: PeopleService):
        self.people_service = people_service

    async def get_tools(self, readonly_context: Optional[ReadonlyContext] = None) -> list[BaseTool]:
        
        async def _search_contacts_tool(query: str, read_mask: str, page_token: Optional[str] = None, tool_context: ToolContext = None) -> dict:
            """Searches for contacts in the user's Google Contacts."""
            user_id = tool_context.invocation_context.session.user_id
            
            # De toolset verzamelt de parameters van de LLM en geeft ze als een model door
            validated_input = SearchContactsQuery(query=query, read_mask=read_mask, page_token=page_token)
            
            return await self.people_service.search_contacts(user_id=user_id, query=validated_input)

        tools = [
            FunctionTool(func=_search_contacts_tool, name="people_search_contacts")
        ]
        return tools