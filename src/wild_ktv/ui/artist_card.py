from PyQt6.QtWidgets import QVBoxLayout
from qfluentwidgets import CardWidget, TitleLabel, CaptionLabel

from wild_ktv.provider import Artist

class ArtistCard(CardWidget):
    def __init__(self, artist: Artist, parent=None):
        super().__init__(parent)
        self.artist = artist

        self.setFixedSize(150, 80)
        self.titleLabel = CaptionLabel(artist.name)
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.addWidget(self.titleLabel)