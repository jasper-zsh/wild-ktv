import os
import asyncio
import logging
from kivy.lang import Builder
from kivy.app import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button, ButtonBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from wild_ktv.model import async_session, Song

logger = logging.getLogger(__name__)

Builder.load_file(os.path.join(os.path.dirname(__file__), 'song.kv'))

class SongCard(RecycleDataViewBehavior, ButtonBehavior, BoxLayout):
    song = ObjectProperty(None)

    def refresh_view_attrs(self, rv, index, data):
        song: Song = data['song']
        self.song = song
        return super().refresh_view_attrs(rv, index, data)
    
    def on_release(self):
        logger.info(f'Pressed {self.song.id} {self.song.name}')