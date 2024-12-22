import sys
import asyncio
import logging

from qasync import QEventLoop, QApplication

from wild_ktv.ui.main_window import MainWindow
from wild_ktv import share

logging.basicConfig(level=logging.INFO)

app = QApplication(sys.argv)
loop = QEventLoop(app)
asyncio.set_event_loop(loop)

share.init()

app_close_event = asyncio.Event()
app.aboutToQuit.connect(app_close_event.set)

window = MainWindow()
window.show()

with loop:
    loop.run_until_complete(app_close_event.wait())