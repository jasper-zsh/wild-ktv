import logging

from kivy.core.video.video_ffpyplayer import VideoFFPy
from kivy.resources import resource_find
from kivy.uix.video import Video as KivyVideo

logger = logging.getLogger(__name__)

class EnhancedVideo(KivyVideo):
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
                self._video = VideoFFPy(filename=filename, **self.options)
                self._video.volume = self.volume
                self._video.bind(on_load=self._on_load,
                                on_frame=self._on_video_frame,
                                on_eos=self._on_eos)
                if self.state == 'play' or self.play:
                    self._video.play()
                self.duration = 1.
                self.position = 0.
        except Exception as ex:
            logger.error(f'Failed to load video: {ex}', exc_info=ex)

    def select_audio_track(self, track_id: int):
        self._video._ffplayer.request_channel('audio', 'open', track_id)