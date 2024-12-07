import os
import logging
import asyncio
import aiohttp
import aiofiles

from kivy.lang import Builder
from kivy.app import App
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.screenmanager import Screen

from wild_ktv.config import Config
from wild_ktv.uix.video import EnhancedVideo
from wild_ktv.uix.lrc import LyricsView
from wild_ktv.model import async_session, Song
from wild_ktv import config
from wild_ktv.lyrics.provider.kg import KugouLyricsProvider
from wild_ktv.lyrics.provider.qm import QQMusicLyricsProvider
from wild_ktv.lyrics.provider.ne import NeteaseMusicLyricsProvider
from wild_ktv.lyrics.match import match_lyrics
from wild_ktv.lyrics.enum import LyricsFormat
from wild_ktv.lyrics.converter import convert2

logger = logging.getLogger(__name__)

Builder.load_file(os.path.join(os.path.dirname(__file__), 'player.kv'))

class PlayerScreen(Screen):
    current_source = StringProperty()
    orig = BooleanProperty(True)
    video: EnhancedVideo

    def on_kv_post(self, base_widget):
        app = App.get_running_app()
        self.video = app.video
        self.video.bind(
            loaded=self.on_video_loaded,
            position=self.on_position_updated,
        )
        self.ids.container.add_widget(self.video, 1)
        self.lrc = LyricsView()
    
    def on_position_updated(self, instance, value):
        self.lrc.position = value
    
    def on_video_loaded(self, instance, value):
        if not value:
            return
        self.ids.container.remove_widget(self.video)
        self.ids.container.remove_widget(self.lrc)
        if self.video.audio_only:
            logger.info('audio only, show lyrics')
            self.ids.container.add_widget(self.lrc, 1)
            app = App.get_running_app()
            if len(app.playlist) > 0 and app.playlist[0].lrc_path:
                self.lrc.file = app.playlist[0].lrc_path
            else:
                self.lrc.file = ''
                asyncio.create_task(self.fetch_lyrics(app.playlist[0]))
        else:
            logger.info('has video, show video frame')
            self.ids.container.add_widget(self.video, 1)
    
    async def fetch_lyrics(self, song: Song):
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as httpSession:
            providers = [
                KugouLyricsProvider(httpSession),
                QQMusicLyricsProvider(httpSession),
                NeteaseMusicLyricsProvider(httpSession),
            ]
            async with async_session() as session:
                session.add(song)
                found = False
                for provider in providers:
                    try:
                        lyrics = await match_lyrics(provider, song)
                        if lyrics:
                            converted = convert2(lyrics, ['orig'], LyricsFormat.VERBATIMLRC)
                            if len(converted) < 200:
                                continue
                            lrc_path = '.'.join([*song.path.split('.')[:-1], 'lrc'])
                            async with aiofiles.open(os.path.join(config.get('data_root'), lrc_path), 'w', encoding='utf-8') as f:
                                await f.write(converted)
                            song.lrc_path = lrc_path
                            await session.commit()
                            logger.info(f'{provider.__class__.__name__}已生成歌词：{lrc_path}')
                            self.lrc.file = lrc_path
                            break
                    except Exception as ex:
                        logger.error(f'{provider.__class__.__name__}匹配歌词失败：{ex}', exc_info=ex)
                if not found:
                    song.lrc_fails += 1
                    await session.commit()
                    logger.info(f'没有找到歌词：{song.id} {song.name}')