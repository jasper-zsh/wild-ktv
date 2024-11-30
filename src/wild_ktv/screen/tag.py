import os
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

Builder.load_file(os.path.join(os.path.dirname(__file__), 'tag.kv'))

class TagScreen(Screen):
    pass