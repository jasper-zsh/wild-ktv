import logging
import math

from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel, QSizePolicy, QTableWidgetItem
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from qfluentwidgets import SingleDirectionScrollArea, FlowLayout, IndeterminateProgressRing, PipsPager, TableWidget
from qasync import asyncSlot

from wild_ktv.provider import FilterOptions, PageOptions, Song
from wild_ktv import share

logger = logging.getLogger(__name__)

class SongList(QWidget):
    songClicked = pyqtSignal(Song)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setObjectName('song_list')

        self.overlayGrid = QGridLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.titleLabel = QLabel('歌曲列表')
        self.table = TableWidget()
        self.pager = PipsPager(Qt.Orientation.Horizontal)

        self.overlayGrid.addLayout(self.vBoxLayout, 0, 0, 1, 1)
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.table)
        self.vBoxLayout.addWidget(self.pager)
        self.pager.currentIndexChanged.connect(self.pageChanged)
        self.table.verticalHeader().hide()
        self.table.setSelectionMode(TableWidget.SelectionMode.NoSelection)
        headers = ['歌名', '歌手', '标签']
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.itemClicked.connect(self._on_row_clicked)

        self.song_filter = None
        self.page_options = None
        self.cur_page_data = []
    
    @asyncSlot(FilterOptions)
    async def query(self, song_filter: FilterOptions):
        self.song_filter = song_filter
        self.page_options = PageOptions(per_page=20)
        self.pager.setPageNumber(0)
        await self._loadData()
        

    @asyncSlot(int)
    async def pageChanged(self, index: int):
        logger.info(f'page changed {index}')
        page_num = index + 1
        if self.page_options.page_num != page_num:
            self.page_options.page_num = page_num
            await self._loadData()

    async def _loadData(self):
        loading = IndeterminateProgressRing()
        self.overlayGrid.addWidget(loading, 0, 0, 1, 1, Qt.AlignmentFlag.AlignCenter)
        try:
            song_page = await share.context.provider.list_songs(self.song_filter, self.page_options)
            logger.info(f'Got {len(song_page.data)} songs total {song_page.total}')
            old_page_number = self.pager.getPageNumber()
            total_page_number = math.ceil(song_page.total / self.page_options.per_page)
            if total_page_number != old_page_number:
                self.pager.setPageNumber(total_page_number)
            self.table.clearContents()
            self.table.setRowCount(len(song_page.data))
            column_widths = [0.5, 0.3, 0.2]
            self.set_column_widths(column_widths)
            self.cur_page_data = song_page.data
            for i, song in enumerate(song_page.data):
                self.table.setItem(i, 0, QTableWidgetItem(song.name))
                self.table.setItem(i, 1, QTableWidgetItem('/'.join([artist.name for artist in song.artists])))
                self.table.setItem(i, 2, QTableWidgetItem(' '.join([tag.name for tag in song.tags])))
            self.table.verticalScrollBar().setValue(0)
        finally:
            loading.deleteLater()
    
    def set_column_widths(self, percentages):
        self._column_widths = percentages
        # 获取 QTableWidget 的总宽度
        total_width = self.table.viewport().width()

        # 计算每列的宽度
        for col, percentage in enumerate(percentages):
            column_width = int(total_width * percentage)
            self.table.setColumnWidth(col, column_width)

    def resizeEvent(self, event):
        if hasattr(self, '_column_widths'):
            # 在窗口大小变化时动态调整列宽
            self.set_column_widths(self._column_widths)
        super().resizeEvent(event)
    
    def _on_row_clicked(self, item: QTableWidgetItem):
        song = self.cur_page_data[item.row()]
        logger.info(f'Song {song.id} {song.name} clicked')
        self.songClicked.emit(song)