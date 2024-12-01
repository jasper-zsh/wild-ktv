import os
import logging
import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from functools import partial

from kivy.lang import Builder
from kivy.app import App
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
            self.ids.rv.data = [SongCard.build_data(song, on_release=partial(self.on_song_clicked, song)) for song in songs]
    
    def on_song_clicked(self, song: Song):
        logger.info(f'Song {song.id} {song.name} clicked')
        app = App.get_running_app()
        app.add_to_playlist(song)