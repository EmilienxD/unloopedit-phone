try:
    from _b import *

    from src.utils import copy_to_clipboard


    if __name__ == '__main__':
        copy_to_clipboard('testing cliipboard')

except Exception as e:
    print(f"ERROR:{e}")