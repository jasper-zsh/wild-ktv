import os
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

Builder.load_file(os.path.join(os.path.dirname(__file__), 'controlbar.kv'))

class ControlBar(BoxLayout):
    pass