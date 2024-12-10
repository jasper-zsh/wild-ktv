import os
import logging

from kivy.lang import Builder
from kivy.app import App
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import ButtonBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from wild_ktv.provider import Artist

logger = logging.getLogger(__name__)

Builder.load_file(os.path.join(os.path.dirname(__file__), 'artist.kv'))

class ArtistCard(RecycleDataViewBehavior, ButtonBehavior, AnchorLayout):
    artist = ObjectProperty()
    name = StringProperty()
    # callback = ObjectProperty(None)

    def refresh_view_attrs(self, rv, index, data):
        self.artist = data['artist']
        self.name = data['name']
        # self.callback = data.get('on_release')
        return super().refresh_view_attrs(rv, index, data)
    
    # def on_release(self):
    #     if self.callback:
    #         self.callback()
    
    @staticmethod
    def build_data(artist: Artist, on_release=lambda: None):
        return {
            'on_release': on_release,
            'artist': artist,
            'name': artist.name,
            'size': (180, 80),
        }
    