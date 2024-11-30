import os
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from wild_ktv.model import Artist

Builder.load_file(os.path.join(os.path.dirname(__file__), 'artist.kv'))

class ArtistCard(RecycleDataViewBehavior, AnchorLayout):
    _id = NumericProperty()
    name = StringProperty()

    def refresh_view_attrs(self, rv, index, data):
        self._id = data['_id']
        self.name = data['name']
        return super().refresh_view_attrs(rv, index, data)
    
    @staticmethod
    def build_data(artist: Artist):
        return {
            '_id': artist.id,
            'name': artist.name,
            'size': (150, 50),
        }