import os
import logging

from kivy.lang import Builder
from kivy.app import App
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from wild_ktv.model import Song

logger = logging.getLogger(__name__)

Builder.load_file(os.path.join(os.path.dirname(__file__), 'playlist.kv'))

class Playlist(ModalView):
    def on_kv_post(self, base_widget):
        app = App.get_running_app()
        app.bind(playlist=self.on_playlist_changed)
    
    def on_playlist_changed(self, instance, value):
        self.ids.rv.data = [PlaylistItem.build_data(song) for song in value]

class PlaylistItem(RecycleDataViewBehavior, BoxLayout):
    song = ObjectProperty(None)
    name = StringProperty()
    artist = StringProperty()

    def refresh_view_attrs(self, rv, index, data):
        self.song = data['song']
        self.name = data['name']
        self.artist = data['artist']
        return super().refresh_view_attrs(rv, index, data)

    def set_to_top(self, instance):
        idx = list(reversed(self.parent.children)).index(instance.parent)
        app = App.get_running_app()
        app.playlist = [
            app.playlist[0],
            self.song,
            *[x[1] for x in filter(lambda x: x[0] != 0 and x[0] != idx, enumerate(app.playlist))]
        ]

    def remove(self, instance):
        idx = list(reversed(self.parent.children)).index(instance.parent)
        app = App.get_running_app()
        app.playlist = [x[1] for x in filter(lambda x: x[0] != idx, enumerate(app.playlist))]
    
    @staticmethod
    def build_data(song: Song):
        return {
            'song': song,
            'name': song.name,
            'artist': '/'.join([artist.name for artist in song.artists])
        }