import os
import logging
import asyncio

from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload, selectinload, subqueryload

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from wild_ktv.model import Artist, Song, async_session
from wild_ktv.uix.artist import ArtistCard
from wild_ktv.uix.song import SongCard

logger = logging.getLogger(__name__)

Builder.load_file(os.path.join(os.path.dirname(__file__), 'search.kv'))

class SearchScreen(Screen):
    search_task: asyncio.Task

    def __init__(self, **kw):
        super().__init__(**kw)
        self.search_task = None

    def search(self, keyword: str):
        if self.search_task:
            self.search_task.cancel()
        self.search_task = asyncio.create_task(self.do_search(keyword))

    async def do_search(self, keyword):
        async with async_session() as session:
            artists = (await session.scalars(
                select(Artist).where(or_(
                    Artist.pinyin_head.like(f'{keyword}%'),
                    Artist.name.like(f'{keyword}%')
                )).limit(10)
            )).all()
            logger.info(f'Got artists: {artists}')
            songs = (await session.scalars(
                select(Song).where(
                    or_(
                        Song.pinyin_head.like(f'{keyword}%'),
                        Song.name.like(f'{keyword}%')
                    )
                )
                .options(selectinload(Song.artists))
                .options(selectinload(Song.tags))
                .limit(50)
            )).all()
            logger.info(f'Got songs: {songs}')
            self.rebuild(artists, songs)
    
    def rebuild(self, artists: list[Artist], songs: list[Song]):
        self.ids.container.clear_widgets()
        artists_widget = self.build_artists(artists)
        if artists_widget:
            self.ids.container.add_widget(artists_widget)
        songs_widget = self.build_songs(songs)
        if songs_widget:
            self.ids.container.add_widget(songs_widget)

    def build_artists(self, artists: list[Artist]):
        if not artists:
            return None
        widget = ArtistSearchResult()
        for artist in artists:
            card = ArtistCard(**ArtistCard.build_data(artist))
            widget.ids.container.add_widget(card)
        return widget

    def build_songs(self, songs: list[Song]):
        if not songs:
            return None
        widget = SongSearchResult()
        for song in songs:
            card = SongCard(**SongCard.build_data(song))
            widget.ids.container.add_widget(card)
        return widget

class ArtistSearchResult(BoxLayout):
    pass

class SongSearchResult(BoxLayout):
    pass