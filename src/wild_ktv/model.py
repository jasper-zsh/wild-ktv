import os
from typing import List, Optional
from sqlalchemy import Text, Table, ForeignKey, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs

engine = None
session_factory = None

def async_session():
    return session_factory()

async def init(rootPath: str):
    global engine, session_factory
    db_path = os.path.join(rootPath, 'ktv.sqlite3')
    engine = create_async_engine(f'sqlite+aiosqlite:///{db_path}', echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

async def dispose():
    await engine.dispose()

class BaseModel(DeclarativeBase, AsyncAttrs):
    pass

song_artist_table = Table(
    'song_artist',
    BaseModel.metadata,
    Column('song_id', ForeignKey('song.id', ondelete='CASCADE')),
    Column('artist_id', ForeignKey('artist.id', ondelete='CASCADE'))
)

song_tag_table = Table(
    'song_tag',
    BaseModel.metadata,
    Column('song_id', ForeignKey('song.id', ondelete='CASCADE')),
    Column('tag_id', ForeignKey('tag.id', ondelete='CASCADE'))
)

class Song(BaseModel):
    __tablename__ = 'song'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text(collation='NOCASE'), index=True)
    pinyin_head: Mapped[str] = mapped_column(Text(collation='NOCASE'), index=True)
    path: Mapped[str] = mapped_column(Text(collation='NOCASE'), index=True)
    lrc_path: Mapped[Optional[str]] = mapped_column(Text())
    lrc_fails: Mapped[int] = mapped_column(nullable=False, default=0)
    audio_only: Mapped[bool] = mapped_column(nullable=False, default=False)
    corrupt: Mapped[bool] = mapped_column(nullable=False, default=False)
    ai_parsed: Mapped[bool] = mapped_column(nullable=False, default=False)

    artists: Mapped[List['Artist']] = relationship(secondary=song_artist_table)
    tags: Mapped[List['Tag']] = relationship(secondary=song_tag_table)

class Artist(BaseModel):
    __tablename__ = 'artist'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text(collation='NOCASE'), index=True)
    pinyin_head: Mapped[str] = mapped_column(Text(collation='NOCASE'), index=True)

class Tag(BaseModel):
    __tablename__ = 'tag'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text(collation='NOCASE'), index=True)