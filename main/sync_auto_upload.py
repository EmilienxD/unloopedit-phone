from _core import *
import asyncio

from lib.config import Paths
from lib.utils import PLATEFORMS
from lib.dataproc.myvideo import UListMyVideos


def main() -> None:
    ready_filenames = [p.full_name for p in Paths('external/icloud.lnk/automation/_auto_/READY')]
    posted_filenames = [p.full_name for p in Paths('external/icloud.lnk/automation/_auto_/POSTED')]
    all_filenames = ready_filenames + posted_filenames
    
    mvs = UListMyVideos.load(status=UListMyVideos.Statuss.READY)

    def icloud_sender():
        max_videos = 25
        free_storage_limit = 0.1

        storage_details = UListMyVideos.get_icloud_storage_details()

        if free_storage_limit > storage_details['available']:
            return
        
        count = 0
        for mv in mvs:
            for plateform in PLATEFORMS:
                if mv.get_upload_status(plateform) == mv.UploadStatuss.READY:
                    video_path = mv.get_converted_path(plateform, raise_error=True)

                    if video_path.full_name not in all_filenames:
                        mv.send_to_icloud(path=video_path)

                        count += 1
                        if count >= max_videos:
                            return
                        
                        storage_details['used'] += video_path.size / 1_000_000_000
                        storage_details['available'] = storage_details['total'] - storage_details['used']
                        if free_storage_limit > storage_details['available']:
                            return

                    mv.add_url(plateform)    # Will update upload status to INITIATED

    async def mega_sender():
        targeted = UListMyVideos()    # Allow one mega sending per video
        for mv in mvs:
            for plateform in PLATEFORMS:
                ustatus = mv.get_upload_status(plateform)

                if ustatus == mv.UploadStatuss.INITIATED and mv.path.full_name in all_filenames:
                    # Handle iCloud manual uploads
                    mv.add_url(plateform, 'unsync')    # Asume no url associated. Will update upload status to UPLOADED
                    (Paths('external/icloud.lnk/automation/_auto_/READY') * mv.path.full_name).remove(send_to_trash=False, not_exists_ok=True)
                    (Paths('external/icloud.lnk/automation/_auto_/POSTED') * mv.path.full_name).remove(send_to_trash=False, not_exists_ok=True)
                    targeted.append(mv)

                elif ustatus == mv.UploadStatuss.UPLOADED and mv.get_url(plateform):
                    # Handle unsynced videos uploaded but not done
                    targeted.append(mv)
        
        await targeted.done_async(max_concurrent=10)

    icloud_sender()
    asyncio.run(mega_sender())

if __name__ == '__main__':
    main()