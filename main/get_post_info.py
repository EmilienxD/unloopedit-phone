try:
    try:
        from _b import *
    except ImportError:
        pass

    import argparse
    import os


    def get_post_info(input_path: str, raise_error: bool = True) -> str:
        filename = input_path
        for ext in ('.mp4', '.mov', '.webm', '.mkv'):
            filename = filename.removesuffix(ext)
        try:
            platform, account, id = filename.split('=')
            id = os.path.basename(id)
        except Exception as err:
            if raise_error:
                raise ValueError(f"Could not parse post info from filename '{filename}': {err}")
            else:
                return ','.join(('None', 'None', 'None'))
        return ','.join((id, account, platform))


    if __name__ == '__main__':
        parser = argparse.ArgumentParser(description='Get video post info from filename.')
        parser.add_argument('input', help='Video input path or filename')
        parser.add_argument('--error', '-e', action='store_true', help='Raise an error when corrupted metadata found, skip otherwise')
        args = parser.parse_args()
        print(get_post_info(args.input.replace('"', '').replace("'", "").strip(), args.error), end='')

except Exception as e:
    print(f"ERROR:{e}", end='')