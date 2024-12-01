import os

from kivy.lang import Builder
from kivy.app import App
from kivy.uix.screenmanager import Screen

Builder.load_file(os.path.join(os.path.dirname(__file__), 'main.kv'))

class MainScreen(Screen):
    pass