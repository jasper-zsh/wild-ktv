import os
import logging
import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from kivy.lang import Builder
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.uix.screenmanager import Screen

from wild_ktv.model import async_session, Song, Artist
from wild_ktv.uix.song import SongCard

logger = logging.getLogger(__name__)
Builder.load_file(os.path.join(os.path.dirname(__file__), 'artist_songs.kv'))

class ArtistSongsScreen(Screen):
    artist_id = NumericProperty(0)
    artist_name = StringProperty()
    load_task = ObjectProperty(None)

    def on_artist_id(self, instance, value):
        if self.load_task:
            self.load_task.cancel()
        self.load_task = asyncio.create_task(self.load_data(value))
    
    async def load_data(self, artist_id):
        async with async_session() as session:
            artist = await session.scalar(select(Artist).where(Artist.id == artist_id))
            self.artist_name = artist.name
            songs = (await session.scalars(
                select(Song)
                .join(Song.artists)
                .where(Artist.id == artist_id)
                .options(selectinload(Song.artists))
                .options(selectinload(Song.tags))
            )).all()
            self.ids.rv.data = [SongCard.build_data(song) for song in songs]