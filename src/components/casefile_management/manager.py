from typing import List
from src.core.models.casefile import Casefile

# Dit is een placeholder. De daadwerkelijke database-logica voegen we later toe.
FAKE_DB = {}

class CasefileManager:
    def create_casefile(self, name: str, owner_id: str) -> Casefile:
        new_casefile = Casefile(name=name, owner_id=owner_id)
        FAKE_DB[new_casefile.id] = new_casefile
        print(f"Casefile '{new_casefile.name}' created with id {new_casefile.id}")
        return new_casefile

    def get_casefile(self, casefile_id: str) -> Casefile | None:
        return FAKE_DB.get(casefile_id)

    def list_casefiles(self) -> List[Casefile]:
        return list(FAKE_DB.values())
