try:
    from _b import *

    import argparse

    from src import utils
    from src.dataproc.accounts import get_accounts, get_platforms
    from src.dataproc.myvideo import UListMyVideos, MyVideo


    AUTO = '[AUTO]'


    def posts_stats(account: str) -> str:
        existing_account_names = {acc.uniquename for acc in get_accounts()}

        mvs = UListMyVideos.load(('status', 'IN', (UListMyVideos.statuses.READY, UListMyVideos.statuses.DONE)),
                                **({'account': account} if (account in existing_account_names) else {}))
        
        posted_this_month = 0
        posted_today = 0

        now = utils.datetime.now()

        for mv in mvs:
            if mv.is_posted:
                dates = []
                for d in mv.publication_dates.values():
                    try:
                        d = utils.str_to_date(d)
                    except ValueError:
                        continue
                    dates.append(d)
                if dates:
                    date = max(dates)
                    if (date.year == now.year) and (date.month == now.month):
                        posted_this_month += 1
                        if date.day == now.day:
                            posted_today += 1

        # Fetch and sort data
        mvs_map = {mv: {u.name: mv.get_upload_status(u.name) for u in mv.uploaders}
                for mv in sorted(mvs.filter_attrs(status=UListMyVideos.statuses.READY), key=lambda mv: utils.str_to_date(mv.id))}

        total_initiated = 0

        non_candidates: list[MyVideo] = []
        for mv, uss in mvs_map.items():
            is_candidate = False
            for us in uss.values():
                if us == mv.uploadstatuses.INITIATED:
                    total_initiated += 1
                    is_candidate = True
            if not is_candidate:
                non_candidates.append(mv)
        
        for mv in non_candidates:
            mvs_map.pop(mv)

        details: dict = {}
        for mv, uss in mvs_map.items():
            if mv.account not in details:
                details[mv.account] = {}
            details[mv.account][mv] = uss

        platform_len = max(map(len, get_platforms()))

        return f"""
### Posts Stats ###

Date: {utils.date_to_str(now)}
Posted this month: {posted_this_month}
Posted today: {posted_today}
Total INITIATED (on drive): {total_initiated}
Details:
{chr(10).join(
    f"  • [{acc}]:{chr(10)}" + 
    chr(10).join(
        f"    • ({mv.id}):{chr(10)}" +
        chr(10).join(
            f"      • {pl.ljust(platform_len)}: {us.name}"
            for pl, us in uss.items()
        )
        for mv, uss in mv_map.items()
    )
    for acc, mv_map in details.items()
)}
""".strip()

    if __name__ == '__main__':
        parser = argparse.ArgumentParser(description='Get video post info from filename.')
        parser.add_argument('account', nargs='?', type=str, default=AUTO, help='(OPTIONAL) Target account')
        args = parser.parse_args()
        print(posts_stats(args.account), end='')

except Exception as e:
    print(f"ERROR:{e}", end='')
