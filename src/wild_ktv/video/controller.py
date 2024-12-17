import logging
import asyncio

from ffpyplayer.player import MediaPlayer
from ffprobe import FFProbe
from ffprobe.ffprobe import FFStream

from kivy.properties import ListProperty, NumericProperty, BooleanProperty
from kivy.event import EventDispatcher
from kivy.clock import Clock
from kivy.graphics import Rectangle, BindTexture
from kivy.graphics.texture import Texture
from kivy.graphics.fbo import Fbo

from wild_ktv.utils.asyncio import call_async

logger = logging.getLogger(__name__)

YUV_RGB_FS = """
$HEADER$
uniform sampler2D tex_y;
uniform sampler2D tex_u;
uniform sampler2D tex_v;

void main(void) {
    float y = texture2D(tex_y, tex_coord0).r;
    float u = texture2D(tex_u, tex_coord0).r - 0.5;
    float v = texture2D(tex_v, tex_coord0).r - 0.5;
    float r = y +             1.402 * v;
    float g = y - 0.344 * u - 0.714 * v;
    float b = y + 1.772 * u;
    gl_FragColor = vec4(r, g, b, 1.0);
}
"""

class VideoController(EventDispatcher):
    video_tracks: list[FFStream] = ListProperty()
    audio_tracks: list[FFStream] = ListProperty()
    loaded = BooleanProperty(False)
    position = NumericProperty(0)
    duration = NumericProperty(0)
    volume = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_load')
        self.register_event_type('on_frame')
        self.audio_only = False
        self._size = None
        self._texture = None

    def on_frame(self, texture):
        pass

    def on_load(self):
        pass

    async def open(self, file_url: str, audio_only: bool = False):
        # if not file_url.startswith('http'):
        #     probe = FFProbe(file_url)
        #     self.audio_tracks = probe.audio
        #     self.video_tracks = probe.video
        self.audio_only = audio_only
            
        ff_opts = {
            'sn': True,
        }
        player = MediaPlayer(
            file_url,
            callback=self._player_callback,
            ff_opts=ff_opts,
        )
        self._player = player
        if self.audio_only:
            duration = await self.wait_for_metadata('duration')
            logger.info(f'loaded audio only, duration {duration}')
        else:
            out_fmt = await self.wait_for_metadata('src_pix_fmt')
            if isinstance(out_fmt, bytes):
                out_fmt = out_fmt.decode()
            self._out_fmt = out_fmt
            player.set_output_pix_fmt(out_fmt)
            logger.info(f'loaded video, output fmt {out_fmt}')
        self.duration = await self.wait_for_metadata('duration')

        meta = player.get_metadata()
        logger.info(f'metadata {meta}')


        logger.info(f'loaded')
        if self.audio_only:
            self._read_task = call_async(self._read_audio(), logger=logger)
        else:
            self._read_task = call_async(self._read_video(), logger=logger)
    
    async def wait_for_metadata(self, name):
        while True:
            value = self._player.get_metadata().get(name)
            if value:
                return value
    
    async def _read_audio(self):
        while True:
            _, val = self._player.get_frame()
            match val:
                case 'eof':
                    break
                case 'paused':
                    await asyncio.sleep(1./10)
                case _:
                    pts = self._player.get_pts()
                    self.position = pts
                    if pts > 0 and not self.loaded:
                        self.loaded = True
                        self.dispatch('on_load')
                    await asyncio.sleep(1./10)

    async def _read_video(self):
        while True:
            frame, val = self._player.get_frame()
            match val:
                case 'eof':
                    break
                case 'paused':
                    await asyncio.sleep(1./10)
                case _:
                    if frame:
                        self.handle_frame(frame)
                    else:
                        if not val:
                            val = 1 / 30.
                    await asyncio.sleep(val)

    def handle_frame(self, frame):
        img, pts = frame
        if img.get_size() != self._size or self._texture is None:
            self._size = w, h = img.get_size()
            if self._out_fmt == 'yuv420p':
                w2 = int(w / 2)
                h2 = int(h / 2)
                self._tex_y = Texture.create(size=(w, h), colorfmt='luminance')
                self._tex_u = Texture.create(size=(w2, h2), colorfmt='luminance')
                self._tex_v = Texture.create(size=(w2, h2), colorfmt='luminance')
                self._fbo = fbo = Fbo(size=self._size)
                with fbo:
                    BindTexture(texture=self._tex_u, index=1)
                    BindTexture(texture=self._tex_v, index=2)
                    Rectangle(size=fbo.size, texture=self._tex_y)
                fbo.shader.fs = YUV_RGB_FS
                fbo['tex_y'] = 0
                fbo['tex_u'] = 1
                fbo['tex_v'] = 2
                self._texture = fbo.texture
            else:
                self._texture = Texture.create(size=self._size, colorfmt='rgba')
            self._texture.flip_vertical()
            self.loaded = True
            self.dispatch('on_load')
        
        if self._texture:
            if self._out_fmt == 'yuv420p':
                dy, du, dv, _ = img.to_memoryview()
                if dy and du and dv:
                    self._tex_y.blit_buffer(dy, colorfmt='luminance')
                    self._tex_u.blit_buffer(du, colorfmt='luminance')
                    self._tex_v.blit_buffer(dv, colorfmt='luminance')
                    self._fbo.ask_update()
                    self._fbo.draw()
            else:
                self._texture.blit_buffer(img.to_memoryview()[0], colorfmt='rgba')
            self.dispatch('on_frame', self._texture)
    # @property
    # def audio_only(self):
    #     return len(self.video_tracks) == 0

    def _player_callback(self, name, value):
        logger.info(f'player callback {name} {value}')

    def close(self):
        self._ffplayer.close_player()

    def on_video_tracks(self, instance, value):
        logger.info(f'got video tracks: {value}')
    
    def on_audio_tracks(self, instance, value):
        logger.info(f'got audio tracks: {value}')