import os
import logging
import asyncio
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.event import EventDispatcher
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.vkeyboard import VKeyboard
from kivy.uix.textinput import TextInput

from wild_ktv.screen.search import SearchScreen

Builder.load_file(os.path.join(os.path.dirname(__file__), 'topbar.kv'))

logger = logging.getLogger(__name__)

class CustomTextInput(TextInput, EventDispatcher):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_click')

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dispatch('on_click')
        return super().on_touch_down(touch)
    
    def on_click(self):
        pass

class TopBar(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.keyword = ''
        self.keyboard_on = False

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
    
    def on_kv_post(self, base_widget):
        kb = VKeyboard(
            on_key_up=self.vkbinput,
            layout='vkb',
            layout_path=os.path.join(os.path.dirname(__file__)),
        )
        self.kb = kb
    
    def resize_keyboard(self, instance, width):
        scale = width / self.kb.width
        self.kb.scale = scale
        self.kb.pos = (0, 0)

    def show_keyboard(self, *args):
        if not self.keyboard_on:
            self.keyboard_on = True
            app = App.get_running_app()
            main_screen = app.main_screen_manager.get_screen('main')
            main_screen.ids.main_container.add_widget(self.kb)
            
            kb = self.kb
            kb.do_translation = False
            kb.do_rotation = False
            kb.do_scale = False
            kb.rotation = 0
            scale = main_screen.ids.main_container.width / float(kb.width)
            kb.scale = scale
            kb.pos = 0, 0
            main_screen.ids.main_container.bind(width=self.resize_keyboard)
    
    def vkbinput(self, keyboard, keycode, *args):
        app = App.get_running_app()
        match keycode:
            case 'escape':
                main_screen = app.main_screen_manager.get_screen('main')
                main_screen.ids.main_container.remove_widget(self.kb)
                self.keyboard_on = False
            case 'backspace':
                self.ids.keyword.text = self.ids.keyword.text[:-1]
            case 'search':
                self.on_search(self.ids.keyword.text)
            case 'clear':
                self.ids.keyword.text = ''
            case _:
                self.ids.keyword.text += keycode
