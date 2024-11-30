import asyncio
import yaml
from wild_ktv import model
from wild_ktv.app import WildKTVApp

    
async def main():
    with open('config.yaml') as f:
        config = yaml.load(f, Loader=yaml.Loader)
    await model.init(config['data_root'])
    await WildKTVApp().async_run()

asyncio.run(main())