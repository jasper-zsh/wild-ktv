import os
from kivy.lang import Builder
from kivy.app import ObjectProperty, StringProperty
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from wild_ktv.model import Artist

Builder.load_file(os.path.join(os.path.dirname(__file__), 'artist.kv'))

class ArtistCard(RecycleDataViewBehavior, AnchorLayout):
    artist = ObjectProperty(None)

    def refresh_view_attrs(self, rv, index, data):
        artist: Artist = data['artist']
        return super().refresh_view_attrs(rv, index, data)