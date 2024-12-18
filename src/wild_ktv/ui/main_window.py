import asyncio

from qfluentwidgets.components.widgets.frameless_window import FramelessWindow
from qfluentwidgets.window.stacked_widget import StackedWidget
from qfluentwidgets import SearchLineEdit, NavigationInterface, FluentIcon, FluentStyleSheet, FluentWindow, FluentTitleBar, NavigationItemPosition
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QLabel, QFrame, QSizePolicy

from wild_ktv.ui.control_bar import ControlBar

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

        self.mainStack.addWidget(QLabel('MainStack'))

        self.initNavigation()

        FluentStyleSheet.FLUENT_WINDOW.apply(self.mainStack)
        
        self.navigation.setFixedWidth(100)
        self.navigation.setExpandWidth(100)
        self.navigation.setMinimumExpandWidth(100)
        self.navigation.setMaximumWidth(100)
        self.navigation.expand(False)
    
    def initNavigation(self):
        self.navigation.addItem('albums', icon=FluentIcon.LIBRARY, text='歌单')
        self.navigation.addItem('artists', icon=FluentIcon.PEOPLE, text='歌手')
        self.navigation.addItem('songs', icon=FluentIcon.MUSIC, text='歌曲')
        self.navigation.addItem('exit', icon=FluentIcon.CLOSE, text='退出', onClick=self.window().close, position=NavigationItemPosition.BOTTOM)

class MainWindow(FramelessWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.titleBar.hide()

        self.hBoxLayout = QHBoxLayout(self)
        self.rootStack = StackedWidget(self)
        self.hBoxLayout.addWidget(self.rootStack)
        self.mainView = MainView(self)
        self.rootStack.addWidget(self.mainView)

        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)

        FluentStyleSheet.FLUENT_WINDOW.apply(self.rootStack)
        
