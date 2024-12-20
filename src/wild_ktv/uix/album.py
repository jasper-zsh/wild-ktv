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
from kivy.animation import Animation

# from wild_ktv.model import async_session, Song
from wild_ktv.provider import Album
from wild_ktv.uix.tag import Tag

logger = logging.getLogger(__name__)

Builder.load_file(os.path.join(os.path.dirname(__file__), 'album.kv'))

class AlbumCard(RecycleDataViewBehavior, ButtonBehavior, FloatLayout):
    album: Album = ObjectProperty(None)
    name = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_click')
        if 'on_click' in kwargs:
            self.on_click = kwargs['on_click']

    def refresh_view_attrs(self, rv, index, data):
        self.album = data['album']
        self.name = data['name']
        
        return super().refresh_view_attrs(rv, index, data)
    
    @staticmethod
    def build_data(album: Album, on_release=lambda: None):
        return {
            'on_click': on_release,
            'size': (300, 100),
            'album': album,
            'name': album.name,
        }
    
    def on_release(self, *args):
        anim = Animation(r=0, g=0, b=0, a=0, duration=0.05)
        anim += Animation(r=1, g=1, b=1, a=0.5, duration=0.05)
        anim.start(self.canvas.before.children[0])
        self.dispatch('on_click')
    
    def on_click(self):
        pass