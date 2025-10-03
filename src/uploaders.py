from dataclasses import dataclass

from src.dataproc.accounts import get_accounts, Account


# This will replace uploader modules which is not available for phone
@dataclass
class Uploader:
    name: str
    """The name of the uploader"""
    
    @property
    def __name__(self) -> str:
        # For compatibility with imported modules
        return self.name
    
    def get_accounts(self) -> list[Account]:
        return [acc for acc in get_accounts() if self.name in acc.platforms]
    
    def get_account_names(self) -> list[str]:
        return [acc.uniquename for acc in self.get_accounts()]
    
    def get_account_uniquenames(self) -> list[str]:
        return [acc.uniquename for acc in self.get_accounts()]
    

UPLOADERS = [Uploader(name) for name in {p for a in get_accounts() for p in a.platforms}]