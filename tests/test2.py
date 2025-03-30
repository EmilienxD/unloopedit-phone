"""from lib.uploaders.youtube import YouTubeUploader


async def m():
    with YouTubeUploader("eb88") as u:
        await u.upload("C:/Users/Emilien/Desktop/tiktok{{{astroplaneet{{{7446553368266296583.mp4", 'testing title', "A description", ['youtube'], privacy_status='private', notify_subscribers=False)

from asyncio import run

run(m())"""

"""from lib.uploaders.tiktok import TikTokManualUploadManager


with TikTokManualUploadManager('gpt1') as tt:
    tt.upload("C:/Users/Emilien/Desktop/tiktok{{{astroplaneet{{{7446553368266296583.mp4")"""


"""from lib.uploaders.youtube import YouTubeManualUploadManager


with YouTubeManualUploadManager('eb88') as tt:
    tt.upload("C:/Users/Emilien/Desktop/tiktok{{{astroplaneet{{{7446553368266296583.mp4")

"""

"""from lib.uploaders.instagram import InstagramManualUploader


with InstagramManualUploader('space1') as tt:
    tt.upload("C:/Users/Emilien/Desktop/tiktok{{{astroplaneet{{{7446553368266296583.mp4")"""


from lib.uploader.instagram import InstagramUploader


async def m():
    with InstagramUploader("space1") as u:
        u.refresh_long_token()
        input("ded")
        await u.upload("C:/Users/Emilien/Desktop/Python/projects/content_creator/content_automation/core/content_created/FINAL/03-03-2025_22-32-52-68/instagram_03-03-2025_22-32-52-68.mp4", 'testing title')

from asyncio import run

run(m())