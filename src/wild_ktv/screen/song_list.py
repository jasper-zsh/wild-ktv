import os
import logging
import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from functools import partial

from kivy.lang import Builder
from kivy.app import App
from kivy.properties import NumericProperty, ObjectProperty, StringProperty, BooleanProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.recycleview import RecycleView
from kivy.clock import Clock

# from wild_ktv.model import async_session, Song, Artist
from wild_ktv.provider import BaseProvider, Song, FilterOptions, PageOptions
from wild_ktv.uix.song import SongCard

logger = logging.getLogger(__name__)
Builder.load_file(os.path.join(os.path.dirname(__file__), 'song_list.kv'))

class SongListScreen(Screen):
    song_filter = ObjectProperty(None)
    title = StringProperty()
    page = NumericProperty(1)
    has_more = BooleanProperty(True)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.load_task = None

    def on_kv_post(self, base_widget):
        self.ids.rv.bind(scroll_y=self._on_scroll_y)
        return super().on_kv_post(base_widget)

    def on_song_filter(self, instance, value: FilterOptions):
        if self.load_task:
            self.load_task.cancel()
        self.page = 1
        self.has_more = True
        self.load_task = asyncio.create_task(self.load_data(value))
        self.load_task.add_done_callback(self.cb)
    
    def cb(self, *args):
        logger.info(f'async cb: {args}')
        self.load_task = None

    def _on_scroll_y(self, instance, value):
        if value <= 0 and self.has_more and self.load_task is None:
            logger.info(f'load more')
            self.page += 1
            self.load_task = asyncio.create_task(self.load_data(self.song_filter))
            self.load_task.add_done_callback(self.cb)
    
    async def load_data(self, song_filter):
        provider: BaseProvider = App.get_running_app().provider
        song_page = await provider.list_songs(song_filter, PageOptions(page_num=self.page))
        logger.info(f'Got {len(song_page.data)} songs total {song_page.total}')
        rv: RecycleView = self.ids.rv
        if (self.page - 1) * 100 + len(song_page.data) >= song_page.total:
            self.has_more = False
        else:
            self.has_more = True
        if self.page == 1:
            rv.data = []
        else:
            old_height = rv.viewport_size[1]
        rv.data.extend([SongCard.build_data(song, on_release=partial(self.on_song_clicked, song)) for song in song_page.data])
        if self.page == 1:
            rv.scroll_y = 1
        else:
            def scroll(*args):
                offset = rv.convert_distance_to_scroll(0, old_height)[1]
                logger.info(offset)
                rv.scroll_y = offset
            Clock.schedule_once(scroll, 0.5)
        # async with async_session() as session:
        #     artist = await session.scalar(select(Artist).where(Artist.id == artist_id))
        #     self.artist_name = artist.name
        #     songs = (await session.scalars(
        #         select(Song)
        #         .join(Song.artists)
        #         .where(Artist.id == artist_id)
        #         .order_by(Song.pinyin_head)
        #         .options(selectinload(Song.artists))
        #         .options(selectinload(Song.tags))
        #     )).all()
        #     self.ids.rv.data = [SongCard.build_data(song, on_release=partial(self.on_song_clicked, song)) for song in songs]
    
    def on_song_clicked(self, song: Song):
        logger.info(f'Song {song.id} {song.name} clicked')
        app = App.get_running_app()
        app.add_to_playlist(song)