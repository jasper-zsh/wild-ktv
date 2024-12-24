import logging

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QLabel, QGridLayout, QSizePolicy
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from qfluentwidgets import FlowLayout, IndeterminateProgressRing, SingleDirectionScrollArea
from qasync import asyncSlot

from wild_ktv import share
from wild_ktv.provider import FilterOptions, PageOptions
from wild_ktv.ui.artist_card import ArtistCard

logger = logging.getLogger(__name__)

class ArtistList(QWidget):
    songsRequest = pyqtSignal(FilterOptions)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setObjectName('artist_list')

        self.overlayGrid = QGridLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.overlayGrid.addLayout(self.vBoxLayout, 0, 0)
        title = QLabel('歌手')
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
            artist_page = await share.context.provider.list_artists(page_options=PageOptions(per_page=200))
            artists = artist_page.data
            logger.info(f'Got {len(artists)} artists total {artist_page.total}')
            self.flow.removeAllWidgets()
            for artist in artists:
                card = ArtistCard(artist)
                card.clicked.connect(lambda artist=artist: self.songsRequest.emit(FilterOptions(artist=artist.id)))
                self.flow.addWidget(card)
        finally:
            loading.deleteLater()