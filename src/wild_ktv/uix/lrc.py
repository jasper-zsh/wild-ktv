import os
import logging
import asyncio
import aiofiles

import aiofiles.os
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
    loaded = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reset()
    
    def reset(self):
        self.loaded = False
        self._last_pos = 0
        self._cur = 0
        self._cur_word = 0
        self._line_height = 44
        self._lines = []
        if self.ids.container:
            self.ids.container.clear_widgets()
    
    def on_parent(self, instance, value):
        if value:
            self.size = value.size
    
    def on_position(self, instance, value):
        if value - self._last_pos < (1 / 30.):
            return
        if not self.loaded:
            return
        self._last_pos = value
        # for l in self._lines:
        #     if l[0].height != self._lines[self._cur][0].height:
        #         line_height = min(l[0].height, self._lines[self._cur][0].height)
        #         if line_height == 0:
        #             return
        #         else:
        #             self._line_height = line_height
        #             self.relocation()
        #             break
        if self._cur < len(self._lines) - 2:
            cur = self._lines[self._cur][0]
            next = self._lines[self._cur + 1][0]
            if next.pos_start < value:
                next.active = True
                cur.active = False
                self._cur += 1
                self._cur_word = 0
            else:
                cur.active = True
        words = self._lines[self._cur][1]
        if self._cur_word < len(words) - 2:
            if words[self._cur_word + 1].pos_start < value:
                words[self._cur_word + 1].animate()
                self._cur_word += 1
            else:
                words[self._cur_word].animate()
        self.relocation()
        
    
    def relocation(self):
        container = self.ids.container
        if not container:
            return
        container.y = - container.height + self.height / 2 + self._line_height * self._cur + self.y

    def on_kv_post(self, base_widget):
        self.add_line_widgets()
    
    def add_line_widgets(self):
        self.ids.container.clear_widgets()
        for l in self._lines:
            self.ids.container.add_widget(l[0])
    
    def on_file(self, instance, value: str):
        self.reset()
        if not value:
            return
        file_path = os.path.join(config.get('data_root'), value.replace('\\', os.path.sep))
        asyncio.create_task(self.load_lyrics(file_path))
    
    async def load_lyrics(self, file_path: str):
        if not await aiofiles.os.path.exists(file_path):
            logger.warning(f'lyrics file {file_path} not found')
            return
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            lines = await f.readlines()
            logger.info(f'loaded {len(lines)} from lrc file {file_path}')
            widgets = []
            for line in lines:
                if len(line) > 2 and line[0] == '[' and line[1] >= '0' and line[1] <= '9':
                    lyrics_line, words = parse_lrc_line(line)
                    words.append(LyricsWord())
                    self._lines.append((lyrics_line, words))
                    widgets.append(lyrics_line)
            self._lines.append((LyricsLine(), []))
            if self.ids.container:
                self.add_line_widgets()
            self.loaded = True
        

class LyricsLine(BoxLayout):
    line = StringProperty()
    pos_start = NumericProperty()
    active = BooleanProperty(False)

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

def parse_lrc_line(line: str) -> tuple[LyricsLine, list[LyricsWord]]:
    flag = 'S'
    piece = ''
    stack = []
    result = LyricsLine()
    words = []
    last_p = 0
    for c in line:
        match flag:
            case 'S':
                if c == '[':
                    flag = 'P'
            case 'P':
                if c == ']':
                    result.pos_start = parse_pos(piece)
                    last_p = result.pos_start
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
                    words.append(w)
                    piece = ''
                    flag = 'C'
                else:
                    piece += c
    for word in words:
        result.add_widget(word)
    return result, words