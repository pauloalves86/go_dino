import os
import sys

from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *


class MainWindow(QWidget):
    def __init__(self, qt_app):
        self.qt_app = qt_app

        QWidget.__init__(self)
        self.setWindowTitle('T-Rex Runner AI')
        self.setMinimumWidth(500)
        self.setMinimumHeight(160)

        self.layout = QVBoxLayout()
        self.form_layout = QFormLayout()

        # self.salutations = ['Ahoy', 'Good day', 'Hello', 'Heyo', 'Hi', 'Salutations', 'Wassup', 'Yo']
        # self.salutation = QComboBox(self)
        # self.salutation.addItems(self.salutations)
        # self.form_layout.addRow('&Salutation:', self.salutation)

        # self.recipient = QLineEdit(self)
        # self.recipient.setPlaceholderText('Matey')
        # self.form_layout.addRow('&Recipient:', self.recipient)

        self.greeting = QLabel('', self)
        self.form_layout.addRow('Greeting:', self.greeting)

        # Add the form layout to the main VBox layout
        self.layout.addLayout(self.form_layout)

        # Add stretch to separate the form layout from the button
        self.layout.addStretch(1)

        self.web_view = QWebEngineView()
        html_path = os.path.join(os.path.dirname(__file__), 't-rex_runner.html')
        html_url = QUrl('file://' + html_path)
        self.web_view.setUrl(html_url)
        self.web_view.setObjectName('WebView')
        self.web_view.setObjectName('WebView')
        self.web_view.setMaximumWidth(500)
        self.web_view.setMaximumHeight(160)
        self.form_layout.addRow('Board:', self.web_view)

        # Create a horizontal box layout to hold the button
        self.button_box = QHBoxLayout()

        # Add stretch to push the button to the far right
        self.button_box.addStretch(1)

        # Create the build button with its caption
        self.build_button = QPushButton('&Build Greeting', self)
        self.build_button.clicked.connect(
            lambda: self.web_view.page().runJavaScript('getScore();', lambda x: self.greeting.setText(str(x))))

        self.timer = QTimer()
        self.timer.timeout.connect(
            lambda: self.web_view.page().runJavaScript('simulateKey("keydown", 38); simulateKey("keyup", 38);'))
        self.timer.start(1000)

        # self.timer2 = QTimer()
        # self.timer2.timeout.connect(lambda: self.web_view.load(QUrl(html_url)))
        # self.timer2.start(5000)

        # Add it to the button box
        self.button_box.addWidget(self.build_button)

        # Add the button box to the bottom of the main VBox layout
        self.layout.addLayout(self.button_box)

        # Set the VBox layout as the window's main layout
        self.setLayout(self.layout)

    def run(self):
        self.show()
        self.qt_app.exec_()


def main():
    app = MainWindow(QApplication(sys.argv))
    app.run()


if __name__ == '__main__':
    main()
