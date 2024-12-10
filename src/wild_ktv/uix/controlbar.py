import os
import logging
from kivy.lang import Builder
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation

from wild_ktv.uix.video import EnhancedVideo

logger = logging.getLogger(__name__)

Builder.load_file(os.path.join(os.path.dirname(__file__), 'controlbar.kv'))

class ControlBar(BoxLayout):
    main_screen_manager = ObjectProperty(None)
    player_screen_state = StringProperty('main')
    video: EnhancedVideo = ObjectProperty(None)
    song_name = StringProperty('请点歌')
    song_artist = StringProperty()
    
    def on_kv_post(self, base_widget):
        self.ids.chk_orig.bind(active=self.on_orig_changed)
        app = App.get_running_app()
        app.bind(playlist=self.on_playlist_changed)
        self.video = app.video
        self.video.bind(
            loaded=self.on_video_loaded,
            position=self.on_position_changed,
            duration=self.on_duration_changed,
            volume=self.on_volume_changed,
        )
        self.ids.volume.bind(value=self.on_change_volume)

    def on_main_screen_manager(self, receiver, value: ScreenManager):
        value.bind(current=self.on_main_sm_current_change)
    
    def on_main_sm_current_change(self, instance, value):
        logger.info(f'main screen changed to {value}')
        self.player_screen_state = value
    
    def on_change_volume(self, instance, value):
        self.video.volume = value / 100

    def on_orig_changed(self, instance, value):
        app = App.get_running_app()
        app.orig = value

    def on_video_loaded(self, instance: EnhancedVideo, value):
        self.ids.progress.disabled = not value
        self.ids.volume.disabled = not value
        self.ids.volume.value = instance.volume * 100
    
    def on_duration_changed(self, instance: EnhancedVideo, value):
        self.ids.progress.max = value
    
    def on_position_changed(self, instance, value):
        self.ids.progress.value = value
    
    def on_volume_changed(self, instance, value):
        self.ids.volume.value = value * 100
    
    def on_playlist_changed(self, instance, value):
        if 'btn_playlist' in self.ids:
            anim = Animation(background_color=(0, 0, 0, 0), duration=0.2)
            anim += Animation(background_color=(1, 1, 1, 1), duration=0.2)
            anim.start(self.ids.btn_playlist)
        if len(value) == 0:
            self.song_name = '请点歌'
            self.song_artist = ''
        else:
            self.song_name = value[0].name
            self.song_artist = '/'.join([artist.name for artist in value[0].artists])
