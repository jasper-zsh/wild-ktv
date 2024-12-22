import logging

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QLabel, QGridLayout, QSizePolicy
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from qfluentwidgets import FlowLayout, IndeterminateProgressRing, SingleDirectionScrollArea
from qasync import asyncSlot

from wild_ktv import share
from wild_ktv.provider import FilterOptions
from wild_ktv.ui.album_card import AlbumCard

logger = logging.getLogger(__name__)

class AlbumList(QWidget):
    songsRequest = pyqtSignal(FilterOptions)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setObjectName('album_list')

        self.overlayGrid = QGridLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.overlayGrid.addLayout(self.vBoxLayout, 0, 0)
        title = QLabel('歌单')
        self.vBoxLayout.addWidget(title)

        self.scrollArea = SingleDirectionScrollArea()
        self.scrollArea.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scrollArea.setWidgetResizable(True)
        self.vBoxLayout.addWidget(self.scrollArea)

        container = QWidget()
        self.scrollArea.setWidget(container)
        self.scrollArea.enableTransparentBackground()
        self.flow = FlowLayout(container)

        QTimer.singleShot(0, self.query)
    
    @asyncSlot()
    async def query(self):
        loading = IndeterminateProgressRing()
        self.overlayGrid.addWidget(loading, 0, 0, 1, 1, Qt.AlignmentFlag.AlignCenter)
        try:
            albums = await share.context.provider.list_playlists()
            logger.info(f'Got {len(albums)} albums')
            self.flow.removeAllWidgets()
            for album in albums:
                card = AlbumCard(album)
                card.clicked.connect(lambda album=album: self.songsRequest.emit(FilterOptions(album=album.id)))
                self.flow.addWidget(card)
        finally:
            loading.deleteLater()