import sys
import asyncio
import logging
import locale

from qasync import QEventLoop, QApplication
from PyQt6.QtCore import Qt

from wild_ktv.ui.main_window import MainWindow
from wild_ktv import share
from wild_ktv import model
from wild_ktv import config

logging.basicConfig(level=logging.INFO)


config.load()

QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
app = QApplication(sys.argv)
loop = QEventLoop(app)
asyncio.set_event_loop(loop)

app_close_event = asyncio.Event()
app.aboutToQuit.connect(app_close_event.set)

locale.setlocale(locale.LC_NUMERIC, 'C')

async def run():
    await model.init(config.get('db_path'))
    share.init()

    window = MainWindow()
    # window.show()
    window.showFullScreen()

    share.context.player.init()

    await app_close_event.wait()

loop.run_until_complete(run())

loop.close()