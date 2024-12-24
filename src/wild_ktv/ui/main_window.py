import asyncio
from typing import Union

from qfluentwidgets.components.widgets.frameless_window import FramelessWindow
from qfluentwidgets.window.stacked_widget import StackedWidget
from qfluentwidgets.common.router import qrouter
from qfluentwidgets import SearchLineEdit, NavigationInterface, FluentIcon, FluentIconBase, FluentStyleSheet, FluentWindow, FluentTitleBar, NavigationItemPosition
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QLabel, QFrame, QSizePolicy
from PyQt6.QtGui import QIcon

from wild_ktv.provider import FilterOptions, Song
from wild_ktv.ui.control_bar import ControlBar
from wild_ktv.ui.album_list import AlbumList
from wild_ktv.ui.song_list import SongList
from wild_ktv.ui.artist_list import ArtistList
from wild_ktv.ui.player_view import PlayerView

from wild_ktv import share

class MainView(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.hBoxLayout = QHBoxLayout(self)
        self.navigation = NavigationInterface(self, showMenuButton=False, collapsible=False)

        self.vBoxLayout = QVBoxLayout()
        self.hBoxLayout.addWidget(self.navigation)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        self.searchEdit = SearchLineEdit(self)
        self.mainStack = StackedWidget(self)
        self.vBoxLayout.addWidget(self.searchEdit)
        self.vBoxLayout.addWidget(self.mainStack)
        self.controlBar = ControlBar(self)
        self.vBoxLayout.addWidget(self.controlBar)

        self.albumList = AlbumList()
        self.songList = SongList()
        self.artistList = ArtistList()
        self.albumList.songsRequest.connect(self.songList.query)
        self.albumList.songsRequest.connect(lambda: self.switchTo(self.songList))
        self.artistList.songsRequest.connect(self.songList.query)
        self.artistList.songsRequest.connect(lambda: self.switchTo(self.songList))
        self.songList.songClicked.connect(lambda song: share.context.add_song_to_playlist(song))

        self.initNavigation()

        FluentStyleSheet.FLUENT_WINDOW.apply(self.mainStack)
        
        self.navigation.setFixedWidth(100)
        self.navigation.setExpandWidth(100)
        self.navigation.setMinimumExpandWidth(100)
        self.navigation.setMaximumWidth(100)
        self.navigation.expand(False)
    
    def initNavigation(self):
        self.addSubInterface(self.albumList, FluentIcon.LIBRARY, text='歌单')
        self.addSubInterface(self.artistList, FluentIcon.PEOPLE, text='歌手')
        self.addSubInterface(self.songList, icon=FluentIcon.MUSIC, text='歌曲')
        self.navigation.addItem('exit', icon=FluentIcon.CLOSE, text='退出', onClick=self.window().close, position=NavigationItemPosition.BOTTOM)

    def addSubInterface(self, interface: QWidget, icon: Union[FluentIconBase, QIcon, str], text: str):
        self.mainStack.addWidget(interface)
        routeKey = interface.objectName()
        item = self.navigation.addItem(
            routeKey=routeKey,
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(interface)
        )

        if self.mainStack.count() == 1:
            self.mainStack.currentChanged.connect(self._onCurrentInterfaceChanged)
            self.navigation.setCurrentItem(routeKey)
            qrouter.setDefaultRouteKey(self.mainStack, routeKey)
        
        return item
    
    def switchTo(self, interface: QWidget):
        self.mainStack.setCurrentWidget(interface, popOut=False)

    def _onCurrentInterfaceChanged(self, index: int):
        widget = self.mainStack.widget(index)
        self.navigation.setCurrentItem(widget.objectName())
        qrouter.push(self.mainStack, widget.objectName())

class MainWindow(FramelessWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.titleBar.hide()

        self.hBoxLayout = QHBoxLayout(self)
        self.rootStack = StackedWidget(self)
        self.hBoxLayout.addWidget(self.rootStack)
        self.mainView = MainView(self)
        self.mainView.controlBar.togglePlayer.connect(self._togglePlayer)
        self.playerView = PlayerView(self)
        self.playerView.controlBar.togglePlayer.connect(self._togglePlayer)
        self.rootStack.addWidget(self.mainView)
        self.rootStack.addWidget(self.playerView)

        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)

        FluentStyleSheet.FLUENT_WINDOW.apply(self.rootStack)
    
    def _togglePlayer(self):
        if self.rootStack.currentWidget() == self.mainView:
            self.rootStack.setCurrentWidget(self.playerView)
        else:
            self.rootStack.setCurrentWidget(self.mainView)
        
