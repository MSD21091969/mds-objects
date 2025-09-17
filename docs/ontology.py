# MDSAPP/core/models/ontology.py
from enum import Enum

class CasefileType(str, Enum):
    """
    Defines the high-level types of casefiles.
    """
    ERBAN = "erban"
    RESEARCH = "research"







class WorkflowStatus(str, Enum):
    """
    Defines the possible statuses of a workflow execution.
    """
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"






from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class DirectiveActionType(str, Enum):
    """Defines the types of actions a directive can instruct an agent to take."""
    PAUSE_AGENT = "PAUSE_AGENT"
    MODIFY_PROMPT = "MODIFY_PROMPT"
    THROTTLE_AGENT = "THROTTLE_AGENT"
    OVERRIDE_MODEL = "OVERRIDE_MODEL"

class SystemDirective(BaseModel):
    """
    A real-time directive that can be used to influence or control the behavior
    of agents and system processes.
    """
    id: str = Field(..., description="The unique identifier for the directive.")
    name: str = Field(..., description="A human-readable name for the directive.")
    description: str = Field(..., description="A description of what the directive does.")
    
    target_agent_type: Optional[str] = Field(default="ALL", description="The type of agent this directive targets (e.g., 'ExecutorAgent', 'ALL').")
    
    action_type: DirectiveActionType = Field(..., description="The type of action to be taken.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the action (e.g., a new prompt snippet, a model name).")
    
    is_active: bool = Field(default=False, description="Whether the directive is currently active and should be enforced.")
    
    user_roles_allowed: List[str] = Field(default_factory=list, description="List of user roles allowed to activate/deactivate this directive.")




class CasefileRole(str, Enum):
    """
    Defines the access control roles for a casefile.
    """
    ADMIN = "admin"
    WRITER = "writer"
    READER = "reader"
