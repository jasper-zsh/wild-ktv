import os
from kivy.app import App, ObjectProperty
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager

from wild_ktv.uix.navbar import NavBar
from wild_ktv.uix.topbar import TopBar
from wild_ktv.uix.controlbar import ControlBar
from wild_ktv.screen.artist import ArtistScreen
from wild_ktv.screen.tag import TagScreen
from wild_ktv.screen.search import SearchScreen
from wild_ktv import model

LabelBase.register(DEFAULT_FONT, fn_regular=os.path.join(os.path.dirname(__file__), 'SourceHanSansSC-Regular.ttf'))

class WildKTVApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screen_stack = []
        self.screen_manager = ScreenManager()
        self.screens = {
            'artists': ArtistScreen(name='artists'),
            'tags': TagScreen(name='tags'),
            'search': SearchScreen(name='search'),
        }
        for screen in self.screens.values():
            self.screen_manager.add_widget(screen)

    def build(self):
        root = BoxLayout()
        root.add_widget(NavBar())
        container = BoxLayout(orientation='vertical')
        root.add_widget(container)

        container.add_widget(TopBar())
        container.add_widget(self.screen_manager)
        container.add_widget(ControlBar())
        return root
    
    def nav_push(self, screen: str):
        self.screen_stack.append(self.screen_manager.current)
        self.screen_manager.current = screen
    
    def nav_back(self):
        if len(self.screen_stack) > 1:
            self.screen_manager.current = self.screen_stack.pop()
        else:
            self.screen_manager.current = self.screen_manager.screen_names[0]
