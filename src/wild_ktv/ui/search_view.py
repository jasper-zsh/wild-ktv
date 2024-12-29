from qasync import asyncSlot

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QTableWidgetItem

from qfluentwidgets import FlowLayout, IndeterminateProgressRing, TableWidget

from wild_ktv.provider import FilterOptions, PageOptions, Song
from wild_ktv.ui.artist_card import ArtistCard
from wild_ktv import share

class SearchView(QWidget):
    songsRequest = pyqtSignal(FilterOptions)
    songClicked = pyqtSignal(Song)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setObjectName('search')
        
        self.vBoxLayout = QVBoxLayout(self)
        self.lblArtist = QLabel('歌手')
        self.lblSong = QLabel('歌曲')
        self.artistLayout = FlowLayout()
        self.songTable = TableWidget()
        headers = ['歌名', '歌手', '标签']
        self.songTable.verticalHeader().hide()
        self.songTable.setColumnCount(len(headers))
        self.songTable.setHorizontalHeaderLabels(headers)

        self.vBoxLayout.addWidget(self.lblArtist)
        self.vBoxLayout.addLayout(self.artistLayout)
        self.vBoxLayout.addWidget(self.lblSong)
        self.vBoxLayout.addWidget(self.songTable)

        self.songTable.itemClicked.connect(lambda item: self.songClicked.emit(self.songs[item.row()]))

        self.songs = []

    @asyncSlot(str)
    async def search(self, keyword):
        loading = IndeterminateProgressRing()
        try:
            artist_res = await share.context.provider.list_artists(
                FilterOptions(name=keyword),
                PageOptions(per_page=20),
            )
            self.artistLayout.removeAllWidgets()
            for artist in artist_res.data:
                card = ArtistCard(artist)
                card.clicked.connect(lambda artist=artist: self.songsRequest.emit(FilterOptions(artist=artist.id)))
                self.artistLayout.addWidget(card)
            song_res = await share.context.provider.list_songs(
                FilterOptions(name=keyword),
                PageOptions(per_page=100),
            )
            self.songTable.clearContents()
            self.songTable.setRowCount(len(song_res.data))
            column_widths = [0.5, 0.3, 0.2]
            self.set_column_widths(column_widths)
            self.songs = song_res.data
            for i, song in enumerate(song_res.data):
                self.songTable.setItem(i, 0, QTableWidgetItem(song.name))
                self.songTable.setItem(i, 1, QTableWidgetItem('/'.join([artist.name for artist in song.artists])))
                self.songTable.setItem(i, 2, QTableWidgetItem(' '.join([tag.name for tag in song.tags])))

        finally:
            loading.deleteLater()
    
    def set_column_widths(self, percentages):
        self._column_widths = percentages
        # 获取 QTableWidget 的总宽度
        total_width = self.songTable.viewport().width()

        # 计算每列的宽度
        for col, percentage in enumerate(percentages):
            column_width = int(total_width * percentage)
            self.songTable.setColumnWidth(col, column_width)

    def resizeEvent(self, event):
        if hasattr(self, '_column_widths'):
            # 在窗口大小变化时动态调整列宽
            self.set_column_widths(self._column_widths)
        super().resizeEvent(event)