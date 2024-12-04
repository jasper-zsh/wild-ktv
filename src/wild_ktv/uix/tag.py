import os

from kivy.lang import Builder
from kivy.uix.label import Label

Builder.load_file(os.path.join(os.path.dirname(__file__), 'tag.kv'))

class Tag(Label):
    pass