import os
import logging
import asyncio
from kivy.lang import Builder
from kivy.app import ObjectProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.recycleview import RecycleView
from sqlalchemy import select

from wild_ktv.uix.artist import ArtistCard
from wild_ktv.model import async_session, Artist

logger = logging.getLogger(__name__)

Builder.load_file(os.path.join(os.path.dirname(__file__), 'artist.kv'))

class ArtistScreen(Screen):
    recycle_view: RecycleView = ObjectProperty(None)

    def __init__(self, **kw):
        super().__init__(**kw)
    
    def on_enter(self, *args):
        asyncio.create_task(self.query())
        return super().on_enter(*args)

    async def query(self):
        async with async_session() as session:
            artists = (await session.scalars(
                select(Artist)
                .order_by(Artist.pinyin_head)
                # .limit(100)
            )).all()
            logger.info(f'Got {len(artists)} artists')
            self.recycle_view.data = [ArtistCard.build_data(artist) for artist in artists]
