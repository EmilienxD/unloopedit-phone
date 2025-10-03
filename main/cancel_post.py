try:
    
    from _b import *

    import argparse

    from src.dataproc.myvideo import MyVideo


    def cancel_post(id: str, platform: str) -> str:
        mv = MyVideo.load(id=id, auto_save=True)
        if mv is None:
            raise ValueError(f'Video with ID "{id}" not found.')

        result = mv.cancel_post(platform=platform)
        
        if result is None:
            raise ValueError(f'Platform "{platform}" not found for {mv}. Video was not registered.')
        elif result is True:
            return f'Video successfully cancelled.'
        else:
            return f'Video not initiated or already done.'


    if __name__ == '__main__':
        parser = argparse.ArgumentParser(description='Register a video post URL for a specific platform')
        parser.add_argument('--id', '-i', required=True, help='Video ID')
        parser.add_argument('--platform', '-p', required=True, help='Platform name (e.g., tiktok, youtube)')
        args = parser.parse_args()
        print(cancel_post(args.id.replace('"', '').replace("'", "").strip(), args.platform.replace('"', '').replace("'", "").strip()), end='')

except Exception as e:
    print(f"ERROR:{e}", end='')
