from typing import Generic, TypeVar
from concurrent.futures import Future

class PageOptions:
    def __init__(self, page_num: int = 1, per_page: int = 100):
        self.page_num = page_num
        self.per_page = per_page

class Artist:
    def __init__(self, id: str=None, name: str=''):
        self.id = id
        self.name = name

class Tag:
    def __init__(self, id: str=None, name: str=''):
        self.id = id
        self.name = name

class Song:
    def __init__(
        self, 
        id: str = None,
        name: str = '',
        artists: list[Artist] = [], 
        file_url: str = '', 
        duration: int = None, 
        lang: str = None, 
        tags: list[Tag] = [],
        orig_channel: int = 0,
        audio_only: bool = False,
        lrc_path: str = None
    ):
        self.id = id
        self.name = name
        self.artists = artists
        self.file_url = file_url
        self.duration = duration
        self.lang = lang
        self.tags = tags
        self.orig_channel = orig_channel
        self.audio_only = audio_only
        self.lrc_path = lrc_path

T = TypeVar('T')

class Page(Generic[T]):
    def __init__(self, total: int, data: list[T]):
        self.total = total
        self.data = data

class SongFilter:
    def __init__(
        self,
        pycode: str = None,
        artist: str = None,
        playlist: str = None,
    ):
        self.pycode = pycode
        self.artist = artist
        self.playlist = playlist

class BaseProvider:
    async def list_artists(self, page_options: PageOptions) -> Page[Artist]:
        pass

    async def get_artist(self, id: str) -> Artist:
        pass

    async def list_songs(self, song_filter: SongFilter, page_options: PageOptions) -> Page[Song]:
        pass

    async def get_song(self, song: Song) -> Song:
        pass