from _b import *

from src.dataproc.accounts import get_accounts, add_account, delete_account


print(get_accounts())
add_account('test_uname', 'test_name', 'test_email')

input(get_accounts())
delete_account('test_uname')

print(get_accounts())