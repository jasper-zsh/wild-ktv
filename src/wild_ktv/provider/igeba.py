import logging
import json
import asyncio
from aiohttp import ClientSession, FormData
from . import BaseProvider, PageOptions, Page, Artist, Song, Tag, Album, FilterOptions

logger = logging.getLogger(__name__)

class ForwardServer:
    def __init__(self, file_url: str, host: str = '127.0.0.1', port: int = 0):
        self.file_url = file_url
        self.host = host
        self.port = port
        self.server = None
        self.session = None
        self.initials = []
    
    async def start(self):
        self.server = await asyncio.start_server(self._client_callback, host=self.host, port=self.port)
        addr = self.server.sockets[0].getsockname()
        self.port = addr[1]
        
        self.session = ClientSession(headers={
            'User-Agent': 'Mozilla/3.0 (compatible; Indy Library)'
        })
        info_res = await self.session.head(self.file_url)
        logger.info(f'got video length {info_res.content_length}')
        self.content_length = info_res.content_length
        self.cur = 0
        for i in range(0):
            data = await self._forward_block()
            self.initials.append(data)
        logger.info(f'forwarding on {self.get_forward_url()}')
    
    def get_forward_url(self):
        return f'tcp://{self.host}:{self.port}'

    async def _forward_block(self):
        self.next = self.cur + 2097152
        if self.next > self.content_length:
            self.next = self.content_length
        range = f'bytes={self.cur}-{self.next}'
        logger.info(f'reading range {range} len {self.next - self.cur}')
        res = await self.session.get(self.file_url, headers={
            'Range': range,
        })
        data = await res.read()
        logger.info(f'got data len {len(data)}')
        self.cur = self.next
        return data

    async def _client_callback(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        logger.info(f'client connected for {self.file_url}, sending {len(self.initials)} initial blocks')
        for block in self.initials:
            writer.write(block)
        await writer.drain()
        while self.cur < self.content_length:
            try:
                data = await self._forward_block()
                writer.write(data)
                await writer.drain()
            except:
                logger.info(f'client connection close for {self.file_url}')
                writer.close()
                self.close()
                return
        logger.info(f'forwarding finished {self.file_url}')
        writer.close()
        self.server.close()
        await self.session.close()

class IGebaProvider(BaseProvider):
    def __init__(self):
        self.client = ClientSession(
            loop=asyncio.get_event_loop(),
            base_url='http://app.ige8.net',
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
                'Origin': 'local://c',
            },
        )

    def _build_filter_params(self, filter_options: FilterOptions):
        f = {}
        if filter_options.name:
            f['Name'] = filter_options.name
        if filter_options.artist:
            f['Package'] = {
                'Type': 1,
                'Id': int(filter_options.artist),
            }
        if filter_options.album:
            parts = filter_options.album.split('-')
            f['Package'] = {
                'Type': int(parts[0]),
                'Id': int(parts[1]),
            }
        return f
    
    async def list_artists(self, artist_filter = None, page_options = None):
        if not artist_filter:
            artist_filter = FilterOptions(tag='推荐歌星')
        f = self._build_filter_params(artist_filter)
        res = await self.client.post(
            '/cloud.php',
            data=FormData({
                'VER': 6,
                'CMD': 'GET_PACGS',
                'PARAMS': json.dumps({
                    'PackageType': 1,
                    'Filter': f,
                    'Page': {
                        'PageSize': page_options.per_page,
                        'PageNo': page_options.page_num,
                    }
                })
            }),
        )
        res_body = await res.json()
        artists = [Artist(
            id=item['SingerId'],
            name=item['SingerName'],
        ) for item in res_body['List']]
        return Page(total=res_body['Page']['RecordCount'], data=artists)
    
    async def get_artist(self, id):
        res = await self.client.post(
            '/cloud.php',
            data=FormData({
                'VER': 6,
                'CMD': 'GET_PACGINF',
                'PARAMS': json.dumps({
                    'PackageType': 1,
                    'PackageId': id,
                })
            })
        )
        res_data = await res.json()
        return Artist(
            id=str(res_data['SingerId']),
            name=res_data['SingerName'],
        )
    
    async def list_songs(self, song_filter, page_options):
        f = self._build_filter_params(song_filter)
        opts = {
            'Order': [{
                'Hot': 1,
            }],
        }
        if song_filter.album:
            parts = song_filter.album.split('-')
            if parts[0] == '4':
                opts = {}
        if page_options:
            opts['Page'] = {
                'PageNo': page_options.page_num,
                'PageSize': page_options.per_page,
            }
        res = await self.client.post(
            '/cloud.php',
            data=FormData({
                'VER': 6,
                'CMD': 'GET_SONGS',
                'PARAMS': json.dumps({
                    'Filter': f,
                    **opts,
                })
            })
        )
        res_data = await res.json()
        songs = [Song(
            id=item['SongNumber'],
            name=item['SongName'],
            artists=[Artist(name=name) for name in item['SingerName'].split('/')],
            file_url=item['SongNumber'],
            duration=int(item['Duration']),
            lang=item['LanguageName'],
            tags=[Tag(name=name) for name in filter(lambda x: len(x) > 0, [item['MtvStyle'], item['MusicStyle'], item['Tag']])],
            orig_channel=int(item['VoiceChannel'])
        ) for item in res_data['List']]
        return Page(total=res_data['Page']['RecordCount'], data=songs)
    
    async def get_song(self, song):
        res = await self.client.post(
            '/telnet.php',
            data=FormData({
                'VER': '8.0',
                'CMD': 'GET_SONGADDR',
                'PARAMS': json.dumps({
                    'SongNumber': song.file_url,
                })
            })
        )
        res_data = await res.json()
        server = ForwardServer(res_data['FileUrl'])
        await server.start()
        song.file_url = server.get_forward_url()
        return song

    async def list_playlists(self):
        res = await self.client.post(
            '/cloud.php',
            data=FormData({
                'VER': 6,
                'CMD': 'GET_PACGS',
                'PARAMS': json.dumps({
                    'PackageType': 4
                })
            })
        )
        res_data = await res.json()
        result = []
        result.extend([Album(id=f'4-{item['RankId']}', name=item['RankTitle'], cover=item['Picture']) for item in res_data['List']])
        res = await self.client.post(
            '/cloud.php',
            data=FormData({
                'VER': 6,
                'CMD': 'GET_PACGS',
                'PARAMS': json.dumps({
                    'PackageType': 3,
                    'Filter': '',
                    'Page': {
                        'PageSize': 100,
                        'PageNo': 1
                    }
                })
            })
        )
        res_data = await res.json()
        result.extend([Album(
            id=f'3-{item['PlayId']}',
            name=item['PlayTitle'],
            cover=item['Picture']
        ) for item in res_data['List']])
        return result
    
    async def list_manage_actions(self):
        return []