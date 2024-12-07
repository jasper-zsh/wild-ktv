import os
import logging
from kivy.lang import Builder
from kivy.app import App, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import ButtonBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label

from wild_ktv.model import async_session, Song
from wild_ktv.uix.tag import Tag

logger = logging.getLogger(__name__)

Builder.load_file(os.path.join(os.path.dirname(__file__), 'song.kv'))

class SongCard(RecycleDataViewBehavior, ButtonBehavior, FloatLayout):
    song: Song = ObjectProperty(None)
    name = StringProperty()
    artist = StringProperty()
    tags = StringProperty()

    def refresh_view_attrs(self, rv, index, data):
        self.song = data['song']
        self.name = data['name']
        self.artist = data['artist']
        self.tags = data['tags']
        
        return super().refresh_view_attrs(rv, index, data)

    def on_kv_post(self, base_widget):
        self.build_flags()
        return super().on_kv_post(base_widget)
    
    def on_song(self, instance, song):
        if not song:
            return
        if 'flags' in self.ids:
            self.build_flags()
    
    def build_flags(self):
        if not self.song:
            return
        self.ids.flags.clear_widgets()
        if self.song.audio_only:
            self.ids.flags.add_widget(Tag(text='仅音频'))
            if not self.song.lrc_path:
                self.ids.flags.add_widget(Tag(text='无歌词'))
    
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