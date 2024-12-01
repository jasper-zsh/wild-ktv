import os
import logging
from kivy.lang import Builder
from kivy.app import App, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import ButtonBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from wild_ktv.model import async_session, Song

logger = logging.getLogger(__name__)

Builder.load_file(os.path.join(os.path.dirname(__file__), 'song.kv'))

class SongCard(RecycleDataViewBehavior, ButtonBehavior, BoxLayout):
    song = ObjectProperty(None)
    name = StringProperty()
    artist = StringProperty()
    tags = StringProperty()

    def refresh_view_attrs(self, rv, index, data):
        self.song = data['song']
        self.name = data['name']
        self.artist = data['artist']
        self.tags = data['tags']
        return super().refresh_view_attrs(rv, index, data)
    
    @staticmethod
    def build_data(song: Song, on_release=lambda: None):
        return {
            'on_release': on_release,
            'size': (300, 100),
            'song': song,
            'name': song.name,
            'artist': '/'.join([artist.name for artist in song.artists]),
            'tags': ' '.join([tag.name for tag in song.tags]),
        }