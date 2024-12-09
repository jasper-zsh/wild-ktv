import logging
import json
import asyncio
from aiohttp import ClientSession, FormData
from . import BaseProvider, PageOptions, Page, Artist, Song, Tag

logger = logging.getLogger(__name__)

class IGebaProvider(BaseProvider):
    def __init__(self):
        self.client = ClientSession(
            base_url='http://app.ige8.net',
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
                'Origin': 'local://c',
            },
            proxy='http://localhost:8888'
        )
    
    async def list_artists(self, page_options):
        res = await self.client.post(
            '/cloud.php',
            data=FormData({
                'VER': 6,
                'CMD': 'GET_PACGS',
                'PARAMS': json.dumps({
                    'PackageType': 1,
                    'Filter': {
                        'PYCode': '',
                        'Sex': '',
                        'Tag': '推荐歌星',
                        'Region': ''
                    },
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
        f = {}
        if song_filter.pycode:
            f['PYCode'] = song_filter.pycode
        if song_filter.artist:
            f['Package'] = {
                'Type': 1,
                'Id': int(song_filter.artist),
            }
        res = await self.client.post(
            '/cloud.php',
            data=FormData({
                'VER': 6,
                'CMD': 'GET_SONGS',
                'PARAMS': json.dumps({
                    'Filter': f,
                    'Order': [{
                        'Hot': 1,
                    }],
                    'Page': {
                        'PageNo': page_options.page_num,
                        'PageSize': page_options.per_page,
                    }
                })
            })
        )
        res_data = await res.json()
        songs = [Song(
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
        song.file_url = res_data['FileUrl']
        song.file_url = 'tcp://127.0.0.1:7777'
        server = await asyncio.streams.start_server(self._client_connected(res_data['FileUrl']), host='127.0.0.1', port=0)
        addr = server.sockets[0].getsockname()
        song.file_url = f'tcp://{addr[0]}:{addr[1]}'
        return song
    
    def _client_connected(self, real_url: str):
        async def cb(reader, writer):
            logger.info(f'client connected for song {real_url}')
            async with ClientSession(headers={
                'User-Agent': 'Mozilla/3.0 (compatible; Indy Library)'
            }) as session:
                info_res = await session.head(real_url)
                logger.info(f'got video length {info_res.content_length}')
                cur = 0
                while cur < info_res.content_length:
                    next = cur + 2097152
                    if next > info_res.content_length:
                        next = info_res.content_length
                    range = f'bytes={cur}-{next}'
                    logger.info(f'reading range {range} len {next - cur}')
                    res = await session.get(real_url, headers={
                        'Range': range,
                    })
                    data = await res.read()
                    logger.info(f'got data len {len(data)}')
                    writer.write(data)
                    await writer.drain()
                    cur = next
        return cb