import os
import logging
import asyncio
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

from wild_ktv.screen.search import SearchScreen

Builder.load_file(os.path.join(os.path.dirname(__file__), 'topbar.kv'))

logger = logging.getLogger(__name__)

class TopBar(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.keyword = ''

    def on_focus(self, focus: bool):
        if focus:
            app = App.get_running_app()
            if app.screen_manager.current != 'search':
                app.nav_push('search')

    def on_search(self, keyword: str):
        app = App.get_running_app()
        if app.screen_manager.current != 'search':
            app.nav_push('search')
        if self.keyword == keyword:
            return
        screen: SearchScreen = app.screen_manager.get_screen('search')
        screen.search(keyword)
