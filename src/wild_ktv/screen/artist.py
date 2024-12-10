import os
import logging
import asyncio
from functools import partial

from kivy.lang import Builder
from kivy.app import App
from kivy.app import ObjectProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.recycleview import RecycleView
from sqlalchemy import select

from wild_ktv.uix.artist import ArtistCard
# from wild_ktv.model import async_session, Artist
from wild_ktv.provider import BaseProvider, PageOptions, Artist, FilterOptions

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
        provider: BaseProvider = App.get_running_app().provider
        artists = await provider.list_artists(page_options=PageOptions())
        logger.info(f'Got {len(artists.data)} artists total {artists.total}')
        self.recycle_view.data = [ArtistCard.build_data(artist, on_release=partial(self.on_artist_clicked, artist)) for artist in artists.data]
        # async with async_session() as session:
        #     artists = (await session.scalars(
        #         select(Artist)
        #         .order_by(Artist.pinyin_head)
        #         .limit(200)
        #     )).all()
        #     logger.info(f'Got {len(artists)} artists')
        #     self.recycle_view.data = [ArtistCard.build_data(artist, on_release=partial(self.on_artist_clicked, artist)) for artist in artists]
    
    def on_artist_clicked(self, artist: Artist, *args):
        logger.info(f'Clicked artist {artist.id} {artist.name}')
        app = App.get_running_app()
        screen = app.screen_manager.get_screen('song_list')
        screen.title = artist.name
        screen.song_filter = FilterOptions(artist=artist.id)
        app.nav_push(screen.name)
