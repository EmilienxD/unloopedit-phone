
try:
    from _b import *

    import argparse

    from src.utils import copy_to_clipboard
    from src.dataproc.myvideo import MyVideo


    def prepare_post(id: str, platform: str) -> str:
        mv = MyVideo.load(id=id)
        if mv is None:
            raise ValueError(f'Video with ID "{id}" not found.')
        
        copy_to_clipboard(mv.caption)
        
        post_info = ''
        for key, value in mv.get_post_info(platform).items():
            post_info += f'• {key}: {value}\n'

        return f"""
### {mv} Post Info ###

{post_info}

""".strip()


    if __name__ == '__main__':
        parser = argparse.ArgumentParser(description='Prepare a video post for a specific platform')
        parser.add_argument('--id', '-i', required=True, help='Video ID')
        parser.add_argument('--platform', '-p', required=True, help='Platform name (e.g., tiktok, youtube)')
        args = parser.parse_args()
        print(prepare_post(args.id.replace('"', '').replace("'", "").strip(), args.platform.replace('"', '').replace("'", "").strip()), end='')

except Exception as e:
    print(f"ERROR:{e}", end='')