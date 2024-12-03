import os
import logging

from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.stencilview import StencilView
from kivy.clock import Clock
from kivy.animation import Animation

from wild_ktv import config

logger = logging.getLogger(__name__)
Builder.load_file(os.path.join(os.path.dirname(__file__), 'lrc.kv'))

class LyricsView(FloatLayout, StencilView):
    file = StringProperty()
    _lines = ListProperty([])
    position = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._last_pos = 0
    
    def on_parent(self, instance, value):
        if value:
            self.size = value.size
    
    def on_position(self, instance, value):
        if value - self._last_pos < 0.05:
            logger.info('drop pos')
            return
        self._last_pos = value
        container = self.ids.container
        if not container:
            return
        lines = container.children
        matched = 0
        line_height = 999999
        for idx, line in enumerate(lines):
            if line.height < line_height:
                line_height = line.height
            if line.pos_start < self.position:
                if not matched:
                    line.active = True
                    line_num = len(lines) - idx
                    matched = line_num
                    for word in line.children:
                        if self.position > word.pos_start and self.position < word.pos_end:
                            word.animate()
                            break
                else:
                    line.active = False
        container.y = - container.height + self.height / 2 + line_height * matched + self.y

    def on_kv_post(self, base_widget):
        for w in self._lines:
            self.add_widget(w)
    
    def on_file(self, instance, value: str):
        if not value:
            return
        file_path = os.path.join(config.get('data_root'), value.replace('\\', os.path.sep))
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                logger.info(f'loaded {len(lines)} from lrc file {value}')
                widgets = []
                for line in lines:
                    if line[0] == '[' and line[1] >= '0' and line[1] <= '9':
                        widgets.append(LyricsLine(line=line))
                if self.ids.container:
                    self.ids.container.clear_widgets()
                    for w in widgets:
                        self.ids.container.add_widget(w)
                else:
                    self._lines = widgets


class LyricsLine(BoxLayout):
    line = StringProperty()
    pos_start = NumericProperty()
    active = BooleanProperty(False)

    def on_kv_post(self, base_widget):
        self.clear_widgets()
        flag = 'S'
        piece = ''
        stack = []
        widgets = []
        last_p = 0
        for c in self.line:
            match flag:
                case 'S':
                    if c == '[':
                        flag = 'P'
                case 'P':
                    if c == ']':
                        self.pos_start = parse_pos(piece)
                        last_p = self.pos_start
                        piece = ''
                        flag = 'C'
                    else:
                        piece += c
                case 'C':
                    if c == '[':
                        stack.append(piece)
                        piece = ''
                        flag = 'WP'
                    else:
                        piece += c
                case 'WP':
                    if c == ']':
                        p = parse_pos(piece)
                        w = LyricsWord(
                            pos_start=last_p,
                            pos_end=p,
                            text=stack.pop()
                        )
                        last_p = p
                        self.add_widget(w)
                        piece = ''
                        flag = 'C'
                    else:
                        piece += c

def parse_pos(txt: str):
    parts = txt.split(':')
    return int(parts[0]) * 60 + float(parts[1])

class LyricsWord(Label):
    pos_start = NumericProperty()
    pos_end = NumericProperty()
    active = BooleanProperty(False)
    animated = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def animate(self):
        if not self.animated:
            anim = Animation(color=(0, 1, 0, 1), duration=self.pos_end - self.pos_start)
            anim.start(self)
            self.animated = True

    def on_parent(self, instance, value):
        value.bind(active=self.on_active_changed)
    
    def on_active_changed(self, instance, value):
        self.active = value
