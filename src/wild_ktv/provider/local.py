import os
import logging
import asyncio
import aiofiles

from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload

from . import BaseProvider, ManageAction, FilterOptions, Page, Artist, Song, Tag
from wild_ktv.model import async_session, Artist as ArtistModel, Tag as TagModel, Song as SongModel, song_artist_table, song_tag_table
from wild_ktv import config

logger = logging.getLogger(__name__)


class LocalProvider(BaseProvider):
    def _artist_filter_query(self, q, artist_filter: FilterOptions|None):
        if not artist_filter:
            return q
        if artist_filter.name:
            q = q.where(ArtistModel.pinyin_head.like(f'{artist_filter.name}%'))
        return q

    async def list_artists(self, artist_filter = None, page_options = None):
        async with async_session() as session:
            q = select(ArtistModel).order_by(ArtistModel.pinyin_head)
            q = self._artist_filter_query(q, artist_filter)
            cnt = await session.scalar(self._artist_filter_query(select(func.count(ArtistModel.id)).select_from(ArtistModel), artist_filter))
            if page_options:
                q = q.limit(page_options.per_page).offset(page_options.per_page * (page_options.page_num - 1))
            artists = (await session.scalars(q)).all()
            return Page(total=cnt, data=[Artist(id=a.id, name=a.name) for a in artists])
        return []
    
    async def get_artist(self, id):
        return None
    
    def _song_filter_query(self, q, song_filter: FilterOptions|None):
        if not song_filter:
            return q
        if song_filter.name:
            q = q.where(SongModel.pinyin_head.like(f'{song_filter.name}%'))
        if song_filter.artist:
            q = q.join(SongModel.artists).where(ArtistModel.id == int(song_filter.artist))
        return q

    async def list_songs(self, song_filter, page_options):
        base_path = config.get('data_root')
        async with async_session() as session:
            cnt = await session.scalar(self._song_filter_query(select(func.count(SongModel.id)).select_from(SongModel), song_filter))
            q = select(SongModel).order_by(SongModel.pinyin_head).options(selectinload(SongModel.artists)).options(selectinload(SongModel.tags))
            q = self._song_filter_query(q, song_filter)
            if page_options:
                q = q.limit(page_options.per_page).offset(page_options.per_page * (page_options.page_num - 1))
            songs = (await session.scalars(q)).all()
            return Page(total=cnt, data=[Song(
                id=s.id,
                name=s.name,
                artists=[Artist(id=a.id, name=a.name) for a in s.artists],
                file_url=os.path.join(base_path, s.path).replace('/', os.sep).replace('\\', os.sep),
                tags=[Tag(id=t.id, name=t.name) for t in s.tags],
                audio_only=s.audio_only,
                lrc_path=os.path.join(base_path, s.lrc_path).replace('/', os.sep).replace('\\', os.sep) if s.lrc_path else None,
            ) for s in songs])
    
    async def get_song(self, song):
        return song
    
    async def list_playlists(self):
        return []
    
    async def list_manage_actions(self):
        return [
            ManageAction(label='歌手数：', load=self._artist_count),
            ManageAction(label='标签数：', load=self._tag_count),
            ManageAction(label='歌曲数：', load=self._song_count),
            ManageAction(label='有视频的歌曲数：', load=self._song_with_video_count),
            ManageAction(label='仅音频的歌曲数：', load=self._song_without_video_count),
            ManageAction(label='没有歌曲的歌手数：', load=self._no_song_artist_count, action_text='清理', action=self._clear_no_song_artists),
            ManageAction(label='没有歌曲的标签数：', load=self._no_song_tag_count, action_text='清理', action=self._clear_no_song_tags),
            ManageAction(label='没有歌词的歌曲数：', load=self._audio_only_without_lyrics),

        ]
    
    async def _artist_count(self, widget, action):
        async with async_session() as session:
            cnt = await session.scalar(
                select(func.count(ArtistModel.id))
                .select_from(ArtistModel)
            )
            widget.value = str(cnt)
    
    async def _tag_count(self, widget, action):
        async with async_session() as session:
            cnt = await session.scalar(
                select(func.count(TagModel.id))
                .select_from(TagModel)
            )
            widget.value = str(cnt)
    
    async def _song_count(self, widget, action):
        async with async_session() as session:
            cnt = await session.scalar(
                select(func.count(SongModel.id))
                .select_from(SongModel)
            )
            widget.value = str(cnt)
    
    async def _song_with_video_count(self, widget, action):
        async with async_session() as session:
            cnt = await session.scalar(
                select(func.count(SongModel.id))
                .select_from(SongModel)
                .where(SongModel.audio_only == False)
            )
            widget.value = str(cnt)
    
    async def _song_without_video_count(self, widget, action):
        async with async_session() as session:
            cnt = await session.scalar(
                select(func.count(SongModel.id))
                .select_from(SongModel)
                .where(SongModel.audio_only == True)
            )
            widget.value = str(cnt)
    
    async def _no_song_artist_count(self, widget, action):
        async with async_session() as session:
            cnt = await session.scalar(
                select(func.count(ArtistModel.id))
                .select_from(ArtistModel)
                .outerjoin(song_artist_table, ArtistModel.id == song_artist_table.c.artist_id)
                .where(song_artist_table.c.song_id == None)
            )
            widget.value = str(cnt)
    
    async def _clear_no_song_artists(self, widget, action, *args):
        async with async_session() as session:
            await session.execute(
                delete(ArtistModel)
                .where(ArtistModel.id.in_(
                    select(ArtistModel.id)
                    .outerjoin(song_artist_table, ArtistModel.id == song_artist_table.c.artist_id)
                    .where(song_artist_table.c.song_id == None)
                ))
            )
            await session.commit()
        await self._no_song_artist_count(widget, action)
    
    async def _no_song_tag_count(self, widget, action):
        async with async_session() as session:
            cnt = await session.scalar(
                select(func.count(TagModel.id))
                .select_from(TagModel)
                .outerjoin(song_tag_table, TagModel.id == song_tag_table.c.tag_id)
                .where(song_tag_table.c.song_id == None)
            )
            widget.value = str(cnt)
    
    async def _clear_no_song_tags(self, widget, action, *args):
        async with async_session() as session:
            await session.execute(
                delete(TagModel)
                .where(TagModel.id.in_(
                    select(TagModel.id)
                    .outerjoin(song_tag_table, TagModel.id == song_tag_table.c.tag_id)
                    .where(song_tag_table.c.song_id == None)
                ))
            )
            await session.commit()
        await self._no_song_tag_count(widget, action)
    
    async def _audio_only_without_lyrics(self, widget, action):
        async with async_session() as session:
            cnt = await session.scalar(
                select(func.count(SongModel.id))
                .select_from(SongModel)
                .where(SongModel.audio_only == True)
                .where(SongModel.lrc_path == None)
            )
            widget.value = str(cnt)