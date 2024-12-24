from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QMetaObject, pyqtSlot
from PyQt6.QtOpenGLWidgets import QOpenGLWidget

from wild_ktv.ui.control_bar import ControlBar
from wild_ktv import share

class MPVWidget(QOpenGLWidget):
    def __init__(self):
        super().__init__()
    
    def initializeGL(self):
        super().initializeGL()
        share.context.mpv_ctx.update_cb = self.on_update

    @pyqtSlot()
    def maybe_update(self):
        if self.window().isMinimized():
            self.makeCurrent()
            self.paintGL()
            self.context().swapBuffers(self.context().surface())
            self.doneCurrent()
        else:
            self.update()
    
    def paintGL(self):
        super().paintGL()
        # handle = self.windowHandle()
        # if handle:
        #     ratio = handle.devicePixelRatio()
        #     w = int(self.width() * ratio)
        #     h = int(self.height() * ratio)
        share.context.mpv_ctx.render(flip_y=True, opengl_fbo={
            'w': self.width(),
            'h': self.height(),
            'fbo': self.defaultFramebufferObject(),
        })

    def on_update(self, ctx=None):
        QMetaObject.invokeMethod(self, 'maybe_update')

class PlayerView(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)

        self.controlBar = ControlBar()

        # self.videoWidget = QVideoWidget()
        # share.context.player.setVideoOutput(self.videoWidget)
        self.videoWidget = MPVWidget()

        self.vBoxLayout.addWidget(self.videoWidget)
        self.vBoxLayout.addWidget(self.controlBar)

        self.videoWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)