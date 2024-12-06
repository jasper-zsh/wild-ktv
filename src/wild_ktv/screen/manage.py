import os
import logging
import asyncio
import functools
import aiofiles.os
import aiohttp
import aiofiles

from sqlalchemy import select, func, delete

from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout

from wild_ktv.model import async_session, Artist, Song, Tag, song_artist_table, song_tag_table
from wild_ktv import config
from wild_ktv.lyrics.provider.kg import KugouLyricsProvider
from wild_ktv.lyrics.provider.qm import QQMusicLyricsProvider
from wild_ktv.lyrics.provider.ne import NeteaseMusicLyricsProvider
from wild_ktv.lyrics.match import match_lyrics
from wild_ktv.lyrics.enum import LyricsFormat
from wild_ktv.lyrics.converter import convert2

logger = logging.getLogger(__name__)
Builder.load_file(os.path.join(os.path.dirname(__file__), 'manage.kv'))

class ManageScreen(Screen):
    pass

class StatsView(BoxLayout):
    artists = StringProperty('0')
    songs = StringProperty('0')
    tags = StringProperty('0')
    song_with_video = StringProperty('0')
    song_audio_only = StringProperty('0')
    no_song_artists = StringProperty('0')
    no_song_tags = StringProperty('0')
    audio_only_without_lyrics = StringProperty('0')
    fetching_lyrics = BooleanProperty(False)
    fixing_lyrics = BooleanProperty(False)
    fix_lyrics_task = None
    broken_lyrics = StringProperty('0')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fetch_lyrics_task = None

    def on_kv_post(self, base_widget):
        asyncio.create_task(self.load_data())
        return super().on_kv_post(base_widget)
    
    async def load_data(self):
        async with async_session() as session:
            cnt = await session.scalar(
                select(func.count(Artist.id))
                .select_from(Artist)
            )
            self.artists = str(cnt)
            cnt = await session.scalar(
                select(func.count(Tag.id))
                .select_from(Tag)
            )
            self.tags=  str(cnt)
            cnt = await session.scalar(
                select(func.count(Song.id))
                .select_from(Song)
            )
            self.songs = str(cnt)
            cnt = await session.scalar(
                select(func.count(Song.id))
                .select_from(Song)
                .where(Song.audio_only == False)
            )
            self.song_with_video = str(cnt)
            cnt = await session.scalar(
                select(func.count(Song.id))
                .select_from(Song)
                .where(Song.audio_only == True)
            )
            self.song_audio_only = str(cnt)
            cnt = await session.scalar(
                select(func.count(Artist.id))
                .select_from(Artist)
                .outerjoin(song_artist_table, Artist.id == song_artist_table.c.artist_id)
                .where(song_artist_table.c.song_id == None)
            )
            self.no_song_artists = str(cnt)
            cnt = await session.scalar(
                select(func.count(Tag.id))
                .select_from(Tag)
                .outerjoin(song_tag_table, Tag.id == song_tag_table.c.tag_id)
                .where(song_tag_table.c.song_id == None)
            )
            self.no_song_tags = str(cnt)
        await self.load_audio_only_without_lyrics()
            
    
    async def load_audio_only_without_lyrics(self):
        async with async_session() as session:
            cnt = await session.scalar(
                select(func.count(Song.id))
                .select_from(Song)
                .where(Song.audio_only == True)
                .where(Song.lrc_path == None)
            )
            self.audio_only_without_lyrics = str(cnt)

    def clear_no_song_artists(self):
        asyncio.create_task(self._clear_no_song_artists())
    
    async def _clear_no_song_artists(self):
        async with async_session() as session:
            await session.execute(
                delete(Artist)
                .where(Artist.id.in_(
                    select(Artist.id)
                    .outerjoin(song_artist_table, Artist.id == song_artist_table.c.artist_id)
                    .where(song_artist_table.c.song_id == None)
                ))
            )
            await session.commit()
        await self.load_data()

    def clear_no_song_tags(self):
        asyncio.create_task(self._clear_no_song_tags())

    async def _clear_no_song_tags(self):
        async with async_session() as session:
            await session.execute(
                delete(Tag)
                .where(Tag.id.in_(
                    select(Tag.id)
                    .outerjoin(song_tag_table, Tag.id == song_tag_table.c.tag_id)
                    .where(song_tag_table.c.song_id == None)
                ))
            )
            await session.commit()
        await self.load_data()
    
    def fetch_lyrics(self):
        if not self.fetch_lyrics_task:
            self.fetch_lyrics_task = asyncio.create_task(self._fetch_lyrics())
            self.fetching_lyrics = True

    def stop_fetch_lyrics(self):
        if self.fetch_lyrics_task:
            self.fetch_lyrics_task.cancel()
            self.fetch_lyrics_task = None
            self.fetching_lyrics = False

    async def _fetch_lyrics(self):
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as httpSession:
            providers = [
                KugouLyricsProvider(httpSession),
                QQMusicLyricsProvider(httpSession),
                NeteaseMusicLyricsProvider(httpSession),
            ]
            async with async_session() as session:
                songs = (await session.scalars(
                    select(Song)
                    .where(Song.lrc_path == None)
                    .where(Song.audio_only == True)
                    .order_by(Song.lrc_fails)
                )).all()
                for song in songs:
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
                                break
                        except Exception as ex:
                            logger.error(f'{provider.__class__.__name__}匹配歌词失败：{ex}', exc_info=ex)
                    if not found:
                        song.lrc_fails += 1
                        await session.commit()
                        logger.info(f'没有找到歌词：{song.id} {song.name}')
                    await self.load_audio_only_without_lyrics()

    def fix_lyrics(self):
        if not self.fixing_lyrics:
            self.fix_lyrics_task = asyncio.create_task(self._fix_lyrics())
            self.fixing_lyrics = True

    def stop_fix_lyrics(self):
        if self.fix_lyrics:
            self.fix_lyrics_task.cancel()
            self.fixing_lyrics = False

    async def _fix_lyrics(self):
        async with async_session() as session:
            songs = (await session.scalars(
                select(Song)
                .where(Song.lrc_path != None)
            )).all()
            broken = 0
            for song in songs:
                fullpath = os.path.join(config.get('data_root'), song.lrc_path)
                stat = await aiofiles.os.stat(fullpath)
                if stat.st_size < 200:
                    logger.info(f'损坏的歌词：{song.lrc_path} 大小 {stat.st_size}')
                    await aiofiles.os.remove(fullpath)
                    song.lrc_path = None
                    await session.commit()
                    broken += 1
                    self.broken_lyrics = str(broken)
                    

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