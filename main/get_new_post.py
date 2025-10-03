try:
    from _b import *

    import argparse

    from src import utils
    from src.dataproc.accounts import get_accounts
    from src.dataproc.myvideo import UListMyVideos, MyVideo


    AUTO = '[AUTO]'


    def get_new_post(account: str) -> str:
        existing_account_uniquenames = {acc.uniquename for acc in get_accounts()}

        # Fetch and sort data
        mvs_map = {
                mv: uss for mv in sorted(
                UListMyVideos.load_iter(
                    status=UListMyVideos.statuses.READY,
                    **({'account': account} if (account in existing_account_uniquenames) else {})),
                key=lambda mv: utils.str_to_date(mv.id)
            ) if mv.uploadstatuses.INITIATED in (uss := {u.name: mv.get_upload_status(u.name) for u in mv.uploaders}).values()
        }
        if not mvs_map:
            raise ValueError('No MyVideo found.')
        
        # Select best MyVideos
        mv_targets = sorted(mvs_map.items(), key=lambda x: -sum(int(status == MyVideo.uploadstatuses.INITIATED) for status in x[1].values()))
        utils.copy_to_clipboard(mv_targets[0][0].id)
        return chr(10).join((mv.id for mv, _ in mv_targets))


    if __name__ == '__main__':
        parser = argparse.ArgumentParser(description='Get video post info from filename.')
        parser.add_argument('account', nargs='?', type=str, default=AUTO, help='(OPTIONAL) Target account')
        args = parser.parse_args()
        print(get_new_post(args.account), end='')

except Exception as e:
    print(f"ERROR:{e}", end='')