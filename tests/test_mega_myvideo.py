from _core import *
import asyncio
from lib.dataproc.myvideo import UListMyVideos

async def me():
    vs = UListMyVideos.load()
    print(vs[0].cloud_loc)

    #await vs[0].download_from_mega_async(plateforms='youtube')


asyncio.run(me())