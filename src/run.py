import sys
import asyncio

from qasync import QEventLoop, QApplication

from wild_ktv.ui.main_window import MainWindow

app = QApplication(sys.argv)
loop = QEventLoop(app)
asyncio.set_event_loop(loop)

app_close_event = asyncio.Event()
app.aboutToQuit.connect(app_close_event.set)

window = MainWindow()
window.show()

with loop:
    loop.run_until_complete(app_close_event.wait())