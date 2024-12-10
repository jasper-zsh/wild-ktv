import os
import logging
import asyncio
from functools import partial

from kivy.lang import Builder
from kivy.app import App
from kivy.app import ObjectProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.recycleview import RecycleView

from wild_ktv.uix.album import AlbumCard
from wild_ktv.provider import BaseProvider, Album, FilterOptions

logger = logging.getLogger(__name__)

Builder.load_file(os.path.join(os.path.dirname(__file__), 'album.kv'))

class AlbumScreen(Screen):
    recycle_view: RecycleView = ObjectProperty(None)

    def __init__(self, **kw):
        super().__init__(**kw)
    
    def on_enter(self, *args):
        asyncio.create_task(self.query())
        return super().on_enter(*args)

    async def query(self):
        provider: BaseProvider = App.get_running_app().provider
        albums = await provider.list_playlists()
        logger.info(f'Got {len(albums)} albums')
        self.recycle_view.data = [AlbumCard.build_data(album, on_release=partial(self.on_album_clicked, album)) for album in albums]
    
    def on_album_clicked(self, album: Album, *args):
        logger.info(f'Clicked album {album.id} {album.name}')
        app = App.get_running_app()
        screen = app.screen_manager.get_screen('song_list')
        screen.title = album.name
        screen.song_filter = FilterOptions(album=album.id)
        app.nav_push(screen.name)
