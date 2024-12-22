from PyQt6.QtWidgets import QVBoxLayout
from qfluentwidgets import CardWidget, TitleLabel, CaptionLabel

from wild_ktv.provider import Album

class AlbumCard(CardWidget):
    def __init__(self, album: Album, parent=None):
        super().__init__(parent)
        self.album = album

        self.setFixedSize(150, 80)
        self.titleLabel = CaptionLabel(album.name)
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.addWidget(self.titleLabel)