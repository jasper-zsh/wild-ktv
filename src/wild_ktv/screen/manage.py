import os
import logging
import asyncio
import functools
import aiofiles.os
import aiohttp
import aiofiles

from sqlalchemy import select, func, delete

from kivy.lang import Builder
from kivy.app import App
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout

from wild_ktv.model import async_session, Artist, Song, Tag, song_artist_table, song_tag_table
from wild_ktv.provider import BaseProvider, ManageAction
from wild_ktv import config
from wild_ktv.lyrics.provider.kg import KugouLyricsProvider
from wild_ktv.lyrics.provider.qm import QQMusicLyricsProvider
from wild_ktv.lyrics.provider.ne import NeteaseMusicLyricsProvider
from wild_ktv.lyrics.match import match_lyrics
from wild_ktv.lyrics.enum import LyricsFormat
from wild_ktv.lyrics.converter import convert2
from wild_ktv.utils.asyncio import call_async

logger = logging.getLogger(__name__)
Builder.load_file(os.path.join(os.path.dirname(__file__), 'manage.kv'))

class ManageScreen(Screen):
    pass

class StatsView(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fetch_lyrics_task = None

    def on_kv_post(self, base_widget):
        call_async(self._load_data(), logger=logger)
        return super().on_kv_post(base_widget)
    
    async def _load_data(self):
        provider: BaseProvider = App.get_running_app().provider
        actions = await provider.list_manage_actions()
        futures = []
        for action in actions:
            widget = Row(
                label=action.label,
                value=action.value,
                action_text=action.action_text,
            )
            if action.action:
                widget.on_action = functools.partial(self._on_manage_action, widget, action)
            if action.load:
                futures.append(asyncio.create_task(action.load(widget, action)))
            self.add_widget(widget)
        if len(futures) > 0:
            await asyncio.wait(futures)
    
    def _on_manage_action(self, widget, action, *args):
        call_async(action.action(widget, action), logger=logger)
    
    # def fetch_lyrics(self):
    #     if not self.fetch_lyrics_task:
    #         self.fetch_lyrics_task = asyncio.create_task(self._fetch_lyrics())
    #         self.fetching_lyrics = True

    # def stop_fetch_lyrics(self):
    #     if self.fetch_lyrics_task:
    #         self.fetch_lyrics_task.cancel()
    #         self.fetch_lyrics_task = None
    #         self.fetching_lyrics = False

    # async def _fetch_lyrics(self):
    #     async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as httpSession:
    #         providers = [
    #             KugouLyricsProvider(httpSession),
    #             QQMusicLyricsProvider(httpSession),
    #             NeteaseMusicLyricsProvider(httpSession),
    #         ]
    #         async with async_session() as session:
    #             songs = (await session.scalars(
    #                 select(Song)
    #                 .where(Song.lrc_path == None)
    #                 .where(Song.audio_only == True)
    #                 .order_by(Song.lrc_fails)
    #             )).all()
    #             for song in songs:
    #                 found = False
    #                 for provider in providers:
    #                     try:
    #                         lyrics = await match_lyrics(provider, song)
    #                         if lyrics:
    #                             converted = convert2(lyrics, ['orig'], LyricsFormat.VERBATIMLRC)
    #                             if len(converted) < 200:
    #                                 continue
    #                             lrc_path = '.'.join([*song.path.split('.')[:-1], 'lrc'])
    #                             async with aiofiles.open(os.path.join(config.get('data_root'), lrc_path), 'w', encoding='utf-8') as f:
    #                                 await f.write(converted)
    #                             song.lrc_path = lrc_path
    #                             await session.commit()
    #                             logger.info(f'{provider.__class__.__name__}已生成歌词：{lrc_path}')
    #                             break
    #                     except Exception as ex:
    #                         logger.error(f'{provider.__class__.__name__}匹配歌词失败：{ex}', exc_info=ex)
    #                 if not found:
    #                     song.lrc_fails += 1
    #                     await session.commit()
    #                     logger.info(f'没有找到歌词：{song.id} {song.name}')
    #                 await self.load_audio_only_without_lyrics()

    # def fix_lyrics(self):
    #     if not self.fixing_lyrics:
    #         self.fix_lyrics_task = asyncio.create_task(self._fix_lyrics())
    #         self.fixing_lyrics = True

    # def stop_fix_lyrics(self):
    #     if self.fix_lyrics:
    #         self.fix_lyrics_task.cancel()
    #         self.fixing_lyrics = False

    # async def _fix_lyrics(self):
    #     async with async_session() as session:
    #         songs = (await session.scalars(
    #             select(Song)
    #             .where(Song.lrc_path != None)
    #         )).all()
    #         broken = 0
    #         for song in songs:
    #             fullpath = os.path.join(config.get('data_root'), song.lrc_path)
    #             stat = await aiofiles.os.stat(fullpath)
    #             if stat.st_size < 200:
    #                 logger.info(f'损坏的歌词：{song.lrc_path} 大小 {stat.st_size}')
    #                 await aiofiles.os.remove(fullpath)
    #                 song.lrc_path = None
    #                 await session.commit()
    #                 broken += 1
    #                 self.broken_lyrics = str(broken)
                    

class Row(BoxLayout):
    label = StringProperty()
    value = StringProperty()
    action_text = StringProperty()
    

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_action')
    
    def _on_action(self):
        self.dispatch('on_action')
    
    def on_action(self):
        pass