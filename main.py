import sys
import json
from PyQt5 import QtGui

import requests
import threading

from PyQt5 import QtWidgets
from PyQt5.QtCore import QCoreApplication, pyqtSignal
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QMessageBox, QWidget, QMainWindow

from main_ui import Ui_MainWindow


class Dashbord(object):
    def __init__(self):
        self.load_config()

    def load_config(self):
        self.config = {}
        with open("config.json") as f:
            self.config = json.load(f)
        controller = self.config.get("controller", {})
        self.host = controller.get("host")
        self.port = controller.get("port")

    def url(self, path):
        return "http://{}:{}{}".format(self.host, self.port, path)

    def get_proxies(self):
        resp = requests.get(self.url("/proxies"))
        proxies = resp.json()
        pairs = [(i, key) for i, key in enumerate(proxies.get("proxies").keys()) ]
        return pairs

    def select_proxy(self, name):
        params={
            "name": name
        }
        resp = requests.put(self.url("/proxies/Proxy"), json=params)
        print("selected", name, resp)

    def ping(self, proxy):
        url = "/proxies/{}/delay".format(proxy)
        params={
            "url":self.config.get("ping",{}).get("url"),
            "timeout":self.config.get("ping",{}).get("timeout")
        }
        resp = requests.get(self.url(url), params=params)
        print(resp.request.url)
        return resp.json().get("delay", "timeout")


class BenchmarkThread(threading.Thread):
    def __init__(self, dash, signal):
        super().__init__()
        self.dash = dash
        self.signal = signal

    def run(self):
        proxies = self.dash.get_proxies()
        for index, proxy in proxies:
            delay = self.dash.ping(proxy)
            self.signal.emit(index, str(delay))


class MainUI(QMainWindow, Ui_MainWindow):
    signal_update = pyqtSignal(int, str)
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.signal_update.connect(self.update_delay)
    
        self.dashboard = Dashbord()

        try:
            proxies = self.dashboard.get_proxies()
        except Exception as e:
            box = QMessageBox()
            box.setWindowTitle("Error")
            box.setText(str(e))
            box.exec()
            sys.exit()

        self.model = QStandardItemModel(self.tableView_proxies)

        for proxy in proxies:
            proxy_name = QStandardItem(proxy[1])
            proxy_delay = QStandardItem(" ")
            proxy_name.setEditable(False)
            proxy_delay.setEditable(False)
            self.model.appendRow([proxy_name, proxy_delay])

        self.tableView_proxies.setModel(self.model)
        self.tableView_proxies.clicked.connect(self.select_proxy)

        header = self.tableView_proxies.horizontalHeader()       
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        self.benchmark()

        tray = QtWidgets.QSystemTrayIcon(self)
        tray.setIcon(QIcon('logo.png'))
        tray.activated.connect(self.tray_active)

        tray_menu = QtWidgets.QMenu(self)
        act_exit = QtWidgets.QAction(self)
        act_exit.setText("quit")
        act_exit.triggered.connect(self.close)

        act_benchmark = QtWidgets.QAction(self)
        act_benchmark.setText("benchmark")
        act_benchmark.triggered.connect(self.benchmark)

        tray_menu.addAction(act_benchmark)
        tray_menu.addAction(act_exit)

        tray.setContextMenu(tray_menu)
        tray.show()

    def close(self):
        QCoreApplication.exit()

    def tray_active(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            state = self.isHidden()
            self.setHidden(not state)
        elif reason == QtWidgets.QSystemTrayIcon.Trigger:
            pass

    def benchmark(self):
        bm = BenchmarkThread(self.dashboard, self.signal_update)
        bm.setDaemon(True)
        bm.start()

    def update_delay(self, row, msg):
        item = self.model.item(row, 1)
        item.setText(msg)

    def select_proxy(self, e):
        name_item = self.model.item(e.row(), 0)
        name = name_item.text()
        self.dashboard.select_proxy(name)
        self.statusbar.showMessage(name)

    def closeEvent(self, e):
        e.ignore()
        self.setHidden(True)


def main():
    app = QApplication(sys.argv)
    w = MainUI()
    w.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()