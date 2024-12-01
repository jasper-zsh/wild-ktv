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

from wild_ktv.model import Artist

logger = logging.getLogger(__name__)

Builder.load_file(os.path.join(os.path.dirname(__file__), 'artist.kv'))

class ArtistCard(RecycleDataViewBehavior, ButtonBehavior, AnchorLayout):
    artist = ObjectProperty()
    name = StringProperty()

    def refresh_view_attrs(self, rv, index, data):
        self.artist = data['artist']
        self.name = data['name']
        return super().refresh_view_attrs(rv, index, data)
    
    @staticmethod
    def build_data(artist: Artist):
        return {
            'artist': artist,
            'name': artist.name,
            'size': (150, 50),
        }
    
    def on_release(self):
        logger.info(f'Clicked artist {self.artist.id} {self.name}')
        app = App.get_running_app()
        screen = app.screen_manager.get_screen('artist_songs')
        screen.artist_id = self.artist.id
        app.nav_push(screen.name)