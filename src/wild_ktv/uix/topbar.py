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
    def on_search(self, keyword: str):
        logger.info(f'on_search {keyword}')
        app = App.get_running_app()
        if app.screen_manager.current is not 'search':
            app.nav_push('search')
        screen: SearchScreen = app.screen_manager.get_screen('search')
        screen.search(keyword)