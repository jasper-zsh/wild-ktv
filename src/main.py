import asyncio
from wild_ktv import model
from wild_ktv import config
from wild_ktv.app import WildKTVApp

async def main():
    config.load()
    await model.init(config.get('db_path'))
    await WildKTVApp().async_run()

asyncio.run(main())