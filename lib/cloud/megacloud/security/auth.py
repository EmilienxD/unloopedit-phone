from dataclasses import dataclass

from lib.modules.paths import Path


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


def load_accounts() -> list[MegaAccount]:
    config_path = Path(__file__, 'File').parent * "config.json"
    return [MegaAccount(name, **acc) for name, acc in config_path.read(default={}).items()]


ACCOUNTS = load_accounts()
assert len(ACCOUNTS) > 0, 'A minimum of 1 accounts is needed.'


def select_account(account_uniquename: str | None = None) -> MegaAccount:
    assert ACCOUNTS, 'Can not select account from empty list.'
    if account_uniquename is None:
        return ACCOUNTS[0]
    else:
        accs = [acc for acc in ACCOUNTS if acc.uniquename == account_uniquename]
        if accs:
            return ACCOUNTS[0]
        raise TypeError(f"No account found from account_uniquename '{account_uniquename}'")

def rotate_account(old_account: MegaAccount) -> None:
    ACCOUNTS.remove(old_account)
    ACCOUNTS.append(old_account)

