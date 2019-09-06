from PyQt5.QtWidgets import QVBoxLayout, QLabel, QWidget, QPushButton, QMainWindow, QApplication, QMenu, QAction
from PyQt5.QtCore import pyqtSignal, QObject, QRunnable, pyqtSlot, QTimer, QThreadPool

import time
import traceback
import sys
import random

from ui.qt_thread_tsts import Ui_MainWindow

# https://www.learnpyqt.com/courses/concurrent-execution/multithreading-pyqt-applications-qthreadpool/


class WorkerSignals(QObject):
    started = pyqtSignal(str)
    finished = pyqtSignal(int)
    progress = pyqtSignal(int)


class Worker(QRunnable):

    def __init__(self, **kwargs):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        super(Worker, self).__init__()

        self.signals = WorkerSignals()
        self.name = kwargs.get('name', '')
        self.index = kwargs.get('index', '')

    @pyqtSlot()
    def run(self):
        sleep_time = random.random()
        time.sleep(sleep_time)
        self.signals.finished.emit(self.index)


class WorkerFactory(QRunnable):

    def __init__(self, **kwargs):
        super(WorkerFactory, self).__init__()
        self.progress_connector = kwargs.get('progress_connector')
        self.iter_count = kwargs.get('iter_count', 100)
        self.w_thread_pool = kwargs.get('thread_pool')

    @pyqtSlot()
    def run(self):
        for i in range(0, self.iter_count + 1):
            w = Worker(iter_count=100, name=f'Worker {1}', index=1)
            w.signals.finished.connect(self.progress_connector)
            # w.run()
            self.w_thread_pool.start(w)

            w = Worker(iter_count=100, name=f'Worker {2}', index=2)
            w.signals.finished.connect(self.progress_connector)
            # w.run()
            self.w_thread_pool.start(w)

            w = Worker(iter_count=100, name=f'Worker {3}', index=3)
            w.signals.finished.connect(self.progress_connector)
            # w.run()
            self.w_thread_pool.start(w)


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        # Start main label timer
        self.counter = 0
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.recurring_timer)
        self.timer.start()

        # Build thread pool
        self.main_thread_pool = QThreadPool()
        self.main_thread_pool.setMaxThreadCount(1)
        self.worker_thread_pool = QThreadPool()
        self.worker_thread_pool.setMaxThreadCount(3)

        self.p1, self.p2, self.p3, self.pg = 0, 0, 0, 0

        self.bt_start.clicked.connect(self.on_bt_start)
        self._stop = False
        self.bt_stop.clicked.connect(self.on_bt_stop)

        menu = QMenu()
        menu.addAction(QAction('This is Action 1', self))
        menu.addAction(QAction('This is Action 2', self))
        self.bt_drop_down_menu.setMenu(menu)

    def recurring_timer(self):
        self.counter += 1
        self.lbl_main_thread.setText(f"Counter: {self.counter}")

    def worker_progress(self, progress: int):
        if self._stop:
            self.worker_thread_pool.clear()
            self.worker_thread_pool.waitForDone(-1)
        elif progress == 1:
            self.p1 += 1
            self.pg_worker_first.setValue(self.p1)
        elif progress == 2:
            self.p2 += 1
            self.pg_worker_second.setValue(self.p2)
        elif progress == 3:
            self.p3 += 1
            self.pg_worker_third.setValue(self.p3)
        self.pg += 1
        self.pg_global.setValue(self.pg)

    @pyqtSlot()
    def on_bt_start(self):
        self._stop = False
        self.p1, self.p2, self.p3, self.pg = 0, 0, 0, 0
        iter_count = 100
        self.pg_worker_first.setValue(0)
        self.pg_worker_second.setValue(0)
        self.pg_worker_third.setValue(0)
        self.pg_global.setMaximum(iter_count * 3)
        self.pg_global.setValue(0)
        worker_factory = WorkerFactory(
            progress_connector=self.worker_progress, iter_count=iter_count, thread_pool=self.worker_thread_pool
        )
        # worker_factory.run()
        self.main_thread_pool.start(worker_factory)

    @pyqtSlot()
    def on_bt_stop(self):
        self._stop = True

    def check_stop(self):
        return self._stop


app = QApplication([])

window = MainWindow()
window.show()
app.exec_()
