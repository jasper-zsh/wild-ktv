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
    
    @property
    def inst_channel(self):
        if self.orig_channel == 0:
            return 1
        else:
            return 0

class Album:
    def __init__(
        self,
        id: str,
        name: str,
        cover: str = ''
    ):
        self.id = id
        self.name = name
        self.cover = cover

class ManageAction:
    def __init__(
        self,
        label: str,
        value: str = '',
        action_text: str = '',
        action = None,
        load = None,
    ):
        self.label = label
        self.value = value
        self.action_text = action_text
        self.action = action
        self.load = load

T = TypeVar('T')

class Page(Generic[T]):
    def __init__(self, total: int, data: list[T]):
        self.total = total
        self.data = data

class FilterOptions:
    def __init__(
        self,
        name: str = None,
        artist: str = None,
        album: str = None,
        tag: str = None,
    ):
        self.name = name
        self.artist = artist
        self.album = album

class BaseProvider:
    async def list_artists(self, artist_filter: FilterOptions = None, page_options: PageOptions = None) -> Page[Artist]:
        pass

    async def get_artist(self, id: str) -> Artist:
        pass

    async def list_songs(self, song_filter: FilterOptions, page_options: PageOptions) -> Page[Song]:
        pass

    async def get_song(self, song: Song) -> Song:
        pass

    async def list_playlists(self) -> list[Album]:
        pass

    async def list_manage_actions(self) -> list[ManageAction]:
        pass