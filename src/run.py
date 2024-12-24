import sys
import asyncio
import logging

from qasync import QEventLoop, QApplication

from wild_ktv.ui.main_window import MainWindow
from wild_ktv import share
# from wild_ktv import model
# from wild_ktv import config

# def exception_hook(exctype, value, traceback):
#     print(f"未捕获的异常: {exctype}, {value}, {traceback}")
#     sys.__excepthook__(exctype, value, traceback)
# sys.excepthook = exception_hook

logging.basicConfig(level=logging.DEBUG)

# config.load()

app = QApplication(sys.argv)
loop = QEventLoop(app)
asyncio.set_event_loop(loop)


share.init()

app_close_event = asyncio.Event()
app.aboutToQuit.connect(app_close_event.set)

window = MainWindow()
window.show()
    # loop.run_until_complete(model.init(config.get('db_path')))


loop.run_until_complete(app_close_event.wait())

loop.close()