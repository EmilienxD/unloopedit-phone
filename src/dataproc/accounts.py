from dataclasses import dataclass, field

from src.dataproc.com import _DB
from src.exceptions import AccountNotFoundError


ALL_PLATFORMS = ['tiktok', 'youtube', 'x', 'instagram',
                 'facebook', 'threads', 'linkedin',
                 'reddit', 'twitch', 'snapchat',
                 'pinterest', 'discord', 'telegram']


@dataclass
class Account:
    uniquename: str
    """Fictive uniquename"""
    name: str
    """The name of the account"""
    email: str
    """The email of the account"""
    platforms: list[str] = field(default_factory=list)
    """The platforms of the account"""
    metadata: str | None = None
    """Any additionnal info about the account"""
    
    def __post_init__(self) -> None:
        self.platforms = [p.lower() for p in self.platforms if p.lower() in ALL_PLATFORMS]


class AccountsDB(_DB):
    _TABLE_NAME = 'accounts'
    
    @classmethod
    def load_accounts(cls) -> list[Account]:
        cls.connect()
        cls._cursor.execute(f'SELECT * FROM "{cls._TABLE_NAME}"')
        rows = cls._cursor.fetchall()
        columns = [description[0] for description in cls._cursor.description]
        params = [dict(zip(columns, row)) for row in rows]
        for r in params:
            if 'platforms' in r and isinstance(r['platforms'], str):
                r['platforms'] = r['platforms'].split(',') if r['platforms'] else []
        return [Account(**r) for r in params]
    
    @classmethod
    def create_table(cls) -> None:
        cls.connect()
        cls._cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS "{cls._TABLE_NAME}" (
                uniquename VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                platforms TEXT NOT NULL,
                metadata VARCHAR(255)
            );
        ''')
        cls._db.commit()
        
    @classmethod
    def account_exists(cls, uniquename: str) -> bool:
        cls.connect()
        cls._cursor.execute(
            f'SELECT 1 FROM "{cls._TABLE_NAME}" WHERE uniquename = %s LIMIT 1', (uniquename,)
        )
        return cls._cursor.fetchone() is not None

    @classmethod
    def add_account(cls, uniquename: str, name: str, email: str, platforms: list[str] | None = None, metadata: str | None = None, skip_on_exists: bool = False) -> Account:
        if cls.account_exists(uniquename):
            if skip_on_exists:
                return Account(uniquename, name, email, platforms, metadata)
            raise ValueError(f"Account with uniquename '{uniquename}' already exists.")
        if platforms is None:
            platforms = []
        cls.connect()
        cls._cursor.execute(
            f'INSERT INTO "{cls._TABLE_NAME}" (uniquename, name, email, platforms, metadata) VALUES (%s, %s, %s, %s, %s)',
            (uniquename, name, email, ','.join(platforms), metadata)
        )
        cls._db.commit()
        return Account(uniquename, name, email, platforms, metadata)
    
    @classmethod
    def delete_account(cls, uniquename: str) -> None:
        cls.connect()
        cls._cursor.execute(f'DELETE FROM "{cls._TABLE_NAME}" WHERE uniquename = %s', (uniquename,))
        cls._db.commit()

def get_accounts() -> list[Account]:
    global _accounts
    if _accounts is None:
        _accounts = AccountsDB.load_accounts()
    return _accounts

def add_account(
    uniquename: str,
    name: str,
    email: str,
    platforms: list[str] | None = None,
    metadata: str | None = None,
    skip_on_exists: bool = False
) -> Account:
    global _accounts
    if platforms is None:
        platforms = []
    account = AccountsDB.add_account(uniquename, name, email, platforms, metadata, skip_on_exists)
    # Skiping folder creation on phone
    if _accounts is None:
        _accounts = []
    _accounts.append(account)
    return account

def update_account(uniquename: str, name: str | None = None, email: str | None = None, platforms: list[str] | None = None, metadata: str | None = None) -> Account:
    global _accounts
    AccountsDB.connect()
    if not AccountsDB.account_exists(uniquename):
        raise AccountNotFoundError(f"Account with uniquename '{uniquename}' not found.")

    AccountsDB._cursor.execute(
        f'SELECT * FROM "{AccountsDB._TABLE_NAME}" WHERE uniquename = %s', (uniquename,)
    )
    row = AccountsDB._cursor.fetchone()
    columns = [description[0] for description in AccountsDB._cursor.description]
    current_data = dict(zip(columns, row))
    
    if 'platforms' in current_data and isinstance(current_data['platforms'], str):
        current_data['platforms'] = current_data['platforms'].split(',') if current_data['platforms'] else []

    if name is not None:
        current_data['name'] = name
    if email is not None:
        current_data['email'] = email
    if platforms is not None:
        current_data['platforms'] = platforms
    if metadata is not None:
        current_data['metadata'] = metadata
    
    AccountsDB._cursor.execute(
        f'UPDATE "{AccountsDB._TABLE_NAME}" SET name = %s, email = %s, platforms = %s, metadata = %s WHERE uniquename = %s',
        (current_data['name'], current_data['email'], ','.join(current_data['platforms']), current_data['metadata'], uniquename)
    )
    AccountsDB._db.commit()
    
    updated_account = Account(
        uniquename=current_data['uniquename'],
        name=current_data['name'],
        email=current_data['email'],
        platforms=current_data['platforms'],
        metadata=current_data['metadata']
    )
    if _accounts:
        for i, account in enumerate(_accounts):
            if account.uniquename == uniquename:
                _accounts[i] = updated_account
                break
    
    return updated_account

def delete_account(uniquename: str) -> None:
    global _accounts
    AccountsDB.delete_account(uniquename)
    if _accounts:
        _accounts[:] = [a for a in _accounts if a.uniquename != uniquename]

def select_account(uniquename: str | None = None) -> Account:
    assert _accounts, 'Can not select account from empty list.'
    if uniquename is None:
        account = _accounts[0]
        rotate_account(account)
        return account
    else:
        for account in _accounts:
            if account.uniquename == uniquename:
                rotate_account(account)
                return account
        raise AccountNotFoundError(f"No account found from uniquename '{uniquename}'")

def rotate_account(old_account: Account) -> None:
    _accounts.remove(old_account)
    _accounts.append(old_account)

def get_platforms() -> list[str]:
    accounts = get_accounts()
    return list({p for a in accounts for p in a.platforms})


_accounts: list[Account] | None = None