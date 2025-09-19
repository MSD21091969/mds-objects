from enum import Enum

class CasefileRole(str, Enum):
    ADMIN = "admin"
    WRITER = "writer"
    READER = "reader"
