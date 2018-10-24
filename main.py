import math
import os
import pickle
import sys
from typing import List

import neat
from PyQt5.QtCore import *
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *
from neat import nn, population
from neat.config import Config


app = QApplication(sys.argv)


class MainWindow(QWidget):
    LOOP_TIMEOUT_MS = 8
    JUMP = 38
    DUCK = 40
    RESTART = 13

    def __init__(self, qt_app):
        self.qt_app = qt_app

        QWidget.__init__(self)
        self.setWindowTitle('T-Rex Runner AI')
        self.setMinimumSize(500, 400)

        players = ['Trainer', 'Dummy', 'Winner']
        self.combo_box_player = QComboBox(self)
        self.combo_box_player.addItems(players)

        self.label_distance = QLabel('', self)
        self.label_width = QLabel('', self)
        self.label_height = QLabel('', self)
        self.label_speed = QLabel('', self)

        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 't-rex_runner.html'))
        html_url = QUrl('file://' + html_path)
        self.web_view = QWebEngineView()
        self.web_view.setUrl(html_url)
        self.web_view.setObjectName('WebView')
        self.web_view.setMaximumSize(500, 160)

        self.label_move_hist = QLabel('', self)
        self.label_move_hist.setTextInteractionFlags(Qt.TextSelectableByKeyboard)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setMinimumSize(500, 160)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.label_move_hist)

        self.build_button = QPushButton('&Start', self)
        self.build_button.clicked.connect(self.create_player)

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
        self.score = 0
        self.player_name = None

    def create_player(self):
        player_name = self.combo_box_player.currentText()
        if player_name == self.player_name:
            return
        if player_name == 'Dummy':
            self.player = DummyPlayer(self)
        elif player_name == 'Trainer':
            self.player = Trainer(self)
            self.player.start()
        self.player_name = player_name

    def play(self):
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
            self.web_view.page().runJavaScript('getScore();', self.player.game_over)
            self.web_view.page().runJavaScript('Playing();', self.playing)

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

    def jump(self):
        self.last_key = Qt.Key_Up
        event = QKeyEvent(QEvent.KeyPress, Qt.Key_Up, Qt.NoModifier, '', False)
        app.notify(self.web_view.focusProxy(), event)

    def duck(self):
        self.last_key = Qt.Key_Down
        event = QKeyEvent(QEvent.KeyPress, Qt.Key_Up, Qt.NoModifier, '', False)
        app.notify(self.web_view.focusProxy(), event)

    def restart(self):
        self.last_key = Qt.Key_Return
        event = QKeyEvent(QEvent.KeyPress, Qt.Key_Up, Qt.NoModifier, '', False)
        app.notify(self.web_view.focusProxy(), event)

    def release(self):
        if self.last_key:
            event = QKeyEvent(QEvent.KeyRelease, self.last_key, Qt.NoModifier, '', False)
            app.notify(self.web_view.focusProxy(), event)
            self.last_key = None

    def run(self):
        self.show()
        self.qt_app.exec_()


class DummyPlayer(object):
    def __init__(self, window: MainWindow):
        self.window = window

    def update(self):
        decision = (self.window.distance + (self.window.width / 2)) / math.log(max(self.window.speed, 6))
        if 0 < decision < 90:
            if self.window.last_key is None:
                last_move = '({:03d} + ({} / 2)) / ln({:.2f}) = {:.2f}\n'.format(self.window.distance,
                                                                                 self.window.width,
                                                                                 self.window.speed, decision)
                self.window.label_move_hist.setText(last_move + self.window.label_move_hist.text())
                self.window.jump()
        else:
            self.window.release()

    def game_over(self, score):
        pass


class Trainer(QThread):
    def __init__(self, window: MainWindow):
        super().__init__()
        self.net = None
        self.window = window
        self.stop = False
        self.score = 0
        local_dir = os.path.dirname(__file__)
        config = Config(neat.DefaultGenome, neat.DefaultReproduction,
                        neat.DefaultSpeciesSet, neat.DefaultStagnation,
                        os.path.join(local_dir, 'train_config.txt'))
        config.save_best = True
        config.checkpoint_time_interval = 3

        self.pop = population.Population(config)
        self.pop.add_reporter(neat.Checkpointer(1))

    def run(self):
        winner = self.pop.run(self.eval_fitness, 100)
        with open('winner.pkl', 'wb') as f:
            pickle.dump(winner, f)

    def play(self):
        print('play')
        self.stop = False
        self.window.restart()
        self.window.release()
        if not self.window.timer_game_loop.isActive():
            self.window.timer_game_loop.start(self.window.LOOP_TIMEOUT_MS)

    def game_over(self, score):
        print('game over')
        self.score = score
        self.stop = True
        print(score, self.stop)

    def update(self):
        if not self.net:
            return
        value = self.net.activate([self.window.distance, self.window.width, self.window.speed])[0]
        self.window.label_move_hist.setText('{:.2f}'.format(value))
        if value >= 0.5:
            self.window.jump()
        else:
            self.window.release()

    def eval_fitness(self, genomes: List, config):
        for i, g in genomes:
            self.net = nn.FeedForwardNetwork.create(g, config)
            self.play()
            while not self.stop:
                # g.fitness = self.start()
                self.msleep(200)
            print('fitness')
            g.fitness = self.score


def main():
    window = MainWindow(app)
    window.run()


if __name__ == '__main__':
    main()
