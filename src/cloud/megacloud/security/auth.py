from dataclasses import dataclass

from src.config import Paths


@dataclass
class MegaAccount:
    uniquename: str
    """Fictive uniquename"""
    email: str
    """The email of the Mega account"""
    password: str
    """The password of the Mega account"""
    metadata: str | None = None
    """Any additionnal info about the account"""


def load_account() -> MegaAccount:
    return MegaAccount(**{
        'uniquename': Paths.getenv('MEGA_UNIQUENAME'),
        'email': Paths.getenv('MEGA_EMAIL'),
        'password': Paths.getenv('MEGA_PASSWORD'),
        'metadata': Paths.getenv('MEGA_METADATA', None)
    })


ACCOUNT = load_account()
assert ACCOUNT, 'An account is needed.'