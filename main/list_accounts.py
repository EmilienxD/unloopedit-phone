try:
    from _b import *

    from src.dataproc.accounts import get_accounts


    def list_accounts() -> str:
        return ','.join({acc.uniquename for acc in get_accounts()})


    if __name__ == '__main__':
        print(list_accounts(), end='')

except Exception as e:
    print(f"ERROR:{e}", end='')