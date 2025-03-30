from _core import *
import asyncio
from lib.cloud.megacloud import MegaCloud


async def me():
    m = MegaCloud()
    m.login()
    #m.download("automation", "C:/Users/Emilien/Downloads/sync_test/gd", overwrite=True)
    #m.create_folder('z/e/r/m', exists_ok=False)

    #await asyncio.gather(m.upload(r"C:\Users\Emilien\Downloads\sync_test\v", 'l'))

asyncio.run(me())