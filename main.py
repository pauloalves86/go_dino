import os
import sys
import math

from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *


class MainWindow(QWidget):
    LOOP_TIMEOUT_MS = 16
    JUMP = 38
    DUCK = 40
    RESTART = 13

    def __init__(self, qt_app):
        self.qt_app = qt_app

        QWidget.__init__(self)
        self.setWindowTitle('T-Rex Runner AI')
        self.setMinimumSize(500, 400)

        players = ['Dummy', 'Winner', 'Trainer']
        self.combo_box_player = QComboBox(self)
        self.combo_box_player.addItems(players)

        self.label_distance = QLabel('', self)
        self.label_width = QLabel('', self)
        self.label_height = QLabel('', self)
        self.label_speed = QLabel('', self)

        html_path = os.path.join(os.path.dirname(__file__), 't-rex_runner.html')
        html_url = QUrl('file://' + html_path)
        self.web_view = QWebEngineView()
        self.web_view.setUrl(html_url)
        self.web_view.setObjectName('WebView')
        self.web_view.setMaximumSize(500, 160)

        self.label_move_hist = QLabel('', self)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setMinimumSize(500, 160)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.label_move_hist)

        self.build_button = QPushButton('&Start Dummy', self)
        self.build_button.clicked.connect(self.play)

        self.form_layout = QFormLayout()
        self.form_layout.addRow('Player:', self.combo_box_player)
        self.form_layout.addRow('Distance:', self.label_distance)
        self.form_layout.addRow('Width:', self.label_width)
        self.form_layout.addRow('Height:', self.label_height)
        self.form_layout.addRow('Speed:', self.label_speed)
        self.form_layout.addRow('Board:', self.web_view)
        self.form_layout.addRow('Hist:', self.scroll_area)

        self.button_box = QHBoxLayout()
        self.button_box.addStretch(1)
        self.button_box.addWidget(self.build_button)

        self.layout = QVBoxLayout()
        self.layout.addLayout(self.form_layout)
        self.layout.addStretch(1)
        self.layout.addLayout(self.button_box)
        self.setLayout(self.layout)

        self.timer_game_loop = QTimer()
        self.timer_game_loop.timeout.connect(self.game_loop)

        self.player = None
        self.speed = 0
        self.distance = 0
        self.width = 0
        self.height = 0
        self.last_key = None

    def play(self):
        if self.combo_box_player.currentText() == 'Dummy':
            self.player = DummyPlayer(self)
        if self.player:
            self.jump()
            self.timer_game_loop.start(self.LOOP_TIMEOUT_MS)

    def game_loop(self):
        self.web_view.page().runJavaScript('getCurrentSpeed();', self.update_speed)
        self.web_view.page().runJavaScript('getNextObstacle();', self.update_obstacle)
        self.web_view.page().runJavaScript('Crashed();', self.crashed)
        self.player.update()

    def crashed(self, state):
        if state and self.timer_game_loop.isActive():
            self.web_view.page().runJavaScript('Playing();', self.playing)
            self.player.game_over()

    def playing(self, state):
        if state is False and self.timer_game_loop.isActive():
            self.timer_game_loop.stop()

    def update_obstacle(self, info):
        if not info:
            return
        self.distance, self.width, self.height = info
        self.label_distance.setText(str(self.distance))
        self.label_width.setText(str(self.width))
        self.label_height.setText(str(self.height))

    def update_speed(self, speed):
        if not speed:
            return
        self.speed = speed
        self.label_speed.setText('{:.2f}'.format(speed))

    def simulate_key(self, state, key_code):
        source = 'simulateKey("{}", {});'
        self.web_view.page().runJavaScript(source.format(state, key_code))

    def jump(self):
        self.simulate_key('keydown', self.JUMP)
        self.last_key = self.JUMP

    def duck(self):
        self.simulate_key('keydown', self.DUCK)
        self.last_key = self.DUCK

    def restart(self):
        self.simulate_key('keydown', self.RESTART)
        self.last_key = self.RESTART

    def release(self):
        if self.last_key:
            self.simulate_key('keyup', self.last_key)
            self.last_key = None

    def run(self):
        self.show()
        self.qt_app.exec_()


class DummyPlayer(object):
    def __init__(self, window: MainWindow):
        self.window = window

    def update(self):
        decision = (self.window.distance + (self.window.width / 2)) / math.log(max(self.window.speed, 6))
        if 0 < decision < 85:
            if self.window.last_key is None:
                last_move = '({:03d} + ({} / 2)) / ln({:.2f}) = {:.2f}\n'.format(self.window.distance, self.window.width,
                                                                               self.window.speed, decision)
                self.window.label_move_hist.setText(last_move + self.window.label_move_hist.text())
                self.window.jump()
        else:
            self.window.release()

    def game_over(self):
        pass


def main():
    app = MainWindow(QApplication(sys.argv))
    app.run()


if __name__ == '__main__':
    main()
