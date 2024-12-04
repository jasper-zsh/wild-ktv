import logging
import time
from threading import Thread

from kivy.core.video.video_ffpyplayer import VideoFFPy
from kivy.properties import BooleanProperty
from kivy.resources import resource_find
from kivy.uix.video import Video as KivyVideo
from ffprobe import FFProbe
from ffpyplayer.player import MediaPlayer
from ffpyplayer.pic import Image

blank_image = Image(pix_fmt='rgba', size=(320, 240))

logger = logging.getLogger(__name__)

class EnhandedVideoFFPy(VideoFFPy):
    audio_only = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        super().load()
        probe = FFProbe(self.filename)
        self.videos = probe.video
        self.audios = probe.audio
        if len(probe.video) == 0:
            self.audio_only = True
            self._out_fmt = 'rgba'
            logger.info('audio only')
        else:
            self.audio_only = False
            self._out_fmt = probe.video[0].pix_fmt
            logger.info(f'out_fmt {self._out_fmt}')

    def _next_frame_run(self, ffplayer):
        sleep = time.sleep
        trigger = self._trigger
        did_dispatch_eof = False
        wait_for_wakeup = self._wait_for_wakeup
        seek_queue = self._seek_queue
        # video starts in internal paused state

        # fast path, if the source video is yuv420p, we'll use a glsl shader
        # for buffer conversion to rgba
        # wait until we get frame metadata
        while not self._ffplayer_need_quit:
            if self.audio_only:
                duration = ffplayer.get_metadata().get('duration')
                if not duration:
                    wait_for_wakeup(0.005)
                    continue
                break
            else:
                src_pix_fmt = ffplayer.get_metadata().get('src_pix_fmt')
                if not src_pix_fmt:
                    wait_for_wakeup(0.005)
                    continue

                # ffpyplayer reports src_pix_fmt as bytes. this may or may not
                # change in future, so we check for both bytes and str
                if src_pix_fmt in (b'yuv420p', 'yuv420p'):
                    self._out_fmt = 'yuv420p'
                break

        if self._ffplayer_need_quit:
            ffplayer.close_player()
            return

        self._ffplayer = ffplayer
        self._finish_setup()
        # now, we'll be in internal paused state and loop will wait until
        # mainthread unpauses us when finishing setup

        while not self._ffplayer_need_quit:
            try:
                seek_happened = False
                if seek_queue:
                    vals = seek_queue[:]
                    del seek_queue[:len(vals)]
                    percent, precise = vals[-1]
                    ffplayer.seek(
                        percent * ffplayer.get_metadata()['duration'],
                        relative=False,
                        accurate=precise
                    )
                    seek_happened = True
                    did_dispatch_eof = False
                    self._next_frame = None

                # Get next frame if paused:
                if seek_happened and ffplayer.get_pause():
                    ffplayer.set_volume(0.0)  # Try to do it silently.
                    ffplayer.set_pause(False)
                    try:
                        # We don't know concrete number of frames to skip,
                        # this number worked fine on couple of tested videos:
                        to_skip = 6
                        while True:
                            frame, val = ffplayer.get_frame(show=False)
                            # Exit loop on invalid val:
                            if val in ('paused', 'eof'):
                                break
                            # Exit loop on seek_queue updated:
                            if seek_queue:
                                break
                            # Wait for next frame:
                            if frame is None:
                                sleep(0.005)
                                continue
                            # Wait until we skipped enough frames:
                            to_skip -= 1
                            if to_skip == 0:
                                break
                        # Assuming last frame is actual, just get it:
                        frame, val = ffplayer.get_frame(force_refresh=True)
                    finally:
                        ffplayer.set_pause(bool(self._state == 'paused'))
                        # todo: this is not safe because user could have updated
                        # volume between us reading it and setting it
                        ffplayer.set_volume(self._volume)
                # Get next frame regular:
                else:
                    frame, val = ffplayer.get_frame()
                    if self.audio_only:
                        pts = ffplayer.get_pts()
                        if pts > 0:
                            frame = (blank_image, pts)
                            val = 1 / 30.
                        
                        
                    # logger.info(f'got frame {frame} {val}')

                if val == 'eof':
                    if not did_dispatch_eof:
                        self._do_eos()
                        did_dispatch_eof = True
                    wait_for_wakeup(None)
                elif val == 'paused':
                    did_dispatch_eof = False
                    wait_for_wakeup(None)
                else:
                    did_dispatch_eof = False
                    if frame:
                        self._next_frame = frame
                        trigger()
                    else:
                        val = val if val else (1 / 30.)
                    wait_for_wakeup(val)
            except Exception as ex:
                logger.error(f'error playback: {ex}', exc_info=ex)

        ffplayer.close_player()

    def play(self):
        # _state starts empty and is empty again after unloading
        if self._ffplayer:
            # player is already setup, just handle unpausing
            assert self._state in ('paused', 'playing')
            if self._state == 'paused':
                self._ffplayer.set_pause(False)
                self._state = 'playing'
                self._wakeup_thread()
            return

        # we're now either in limbo state waiting for thread to setup,
        # or no thread has been started
        if self._state == 'playing':
            # in limbo, just wait for thread to setup player
            return
        elif self._state == 'paused':
            # in limbo, still unpause for when player becomes ready
            self._state = 'playing'
            self._wakeup_thread()
            return

        # load first unloads
        self.load()
        # if no stream, it starts internally paused, but unpauses itself
        # if stream and we start paused, we sometimes receive eof after a
        # few frames, depending on the stream producer.
        # XXX: This probably needs to be figured out in ffpyplayer, using
        #      ffplay directly works.
        ff_opts = {
            'paused': not self._is_stream,
            'out_fmt': self._out_fmt,
            'sn': True,
            'volume': self._volume,
        }
        ffplayer = MediaPlayer(
            self._filename,
            audio_only=self.audio_only,
            callback=self._player_callback,
            thread_lib='SDL',
            loglevel='info', ff_opts=ff_opts
        )

        # Disabled as an attempt to fix kivy issue #6210
        # self._ffplayer.set_volume(self._volume)

        self._thread = Thread(
            target=self._next_frame_run,
            name='Next frame',
            args=(ffplayer, )
        )
        # todo: remove
        self._thread.daemon = True

        # start in playing mode, but _ffplayer isn't set until ready. We're
        # now in a limbo state
        self._state = 'playing'
        self._thread.start()

class EnhancedVideo(KivyVideo):
    audio_only = BooleanProperty(False)

    def _do_video_load(self, *largs):
        try:
            logger.info('using customized video load')
            self.unload()
            if not self.source:
                self._video = None
                self.texture = None
            else:
                filename = self.source
                # Check if filename is not url
                if '://' not in filename:
                    filename = resource_find(filename)
                self._video = EnhandedVideoFFPy(
                    filename=filename,
                    # ff_opts={'genpts': True},
                    **self.options
                )
                self._video.volume = self.volume
                self._video.bind(
                    on_load=self._on_load,
                    on_frame=self._on_video_frame,
                    on_eos=self._on_eos,
                )
                if self.state == 'play' or self.play:
                    self._video.play()
                self.duration = 1.
                self.position = 0.
        except Exception as ex:
            logger.error(f'Failed to load video: {ex}', exc_info=ex)
    
    def _on_load(self, *largs):
        self.audio_only = self._video.audio_only
        super()._on_load(*largs)

    def select_audio_track(self, track_id: int):
        track_id = track_id + len(self._video.videos)
        try:
            self._video._ffplayer.request_channel('audio', 'open', track_id)
        except Exception as ex:
            logger.error('failed to select audio track: {ex}', exc_info=ex)
