from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QMessageBox, QGridLayout,
                             QMainWindow)
from PyQt6.QtCore import QTimer, QTime, Qt
from PyQt6.QtGui import QFont
import sys

from system.log_instance import LogInstance
from system.timecode import TimeCode

timecode: TimeCode


class View(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 800, 400)
        self.clock = QLabel()
        self.clock.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.clock.setFont(QFont('Arial', 60))

        self.timecode = QLabel()
        self.timecode.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.timecode.setFont(QFont('Arial', 60))

        self.label1 = QLabel()
        self.label1.setStyleSheet('border: 1px solid black;')

        self.label2 = QLabel()
        self.label2.setStyleSheet('border: 1px solid black;')

        self.button = QPushButton('Click Me')

        layout = QGridLayout()
        layout.addWidget(self.clock, 0, 0, 1, 1)
        layout.addWidget(self.timecode, 0, 1, 1, 1)
        layout.addWidget(self.label1, 1, 0, 1, 1)
        layout.addWidget(self.label2, 1, 1, 1, 1)
        # layout.addWidget(self.button, 2, 0, 1, 1)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        clock_timer = QTimer(self)
        clock_timer.timeout.connect(self.show_time)
        clock_timer.start()

    def show_time(self):
        current_time = QTime.currentTime()
        label_time = current_time.toString('hh:mm:ss')
        self.clock.setText(label_time)
        self.timecode.setText(timecode.time_code)
        self.label1.setText(LogInstance.string_data)


class Controller:
    def __init__(self, view):
        self.view = view
        self.duration = 5

        self.view.button.pressed.connect(self.show_msg)

    def show_msg(self):
        self.view.label2.setText(f'I am going to close in {self.duration} seconds.')
        self.view.label2.show()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

        self.msg = QMessageBox()
        self.msg.setText(f'I am going to close in {self.duration} seconds.')
        self.msg.setIcon(QMessageBox.Icon.Information)
        self.msg.exec()

    def update(self):
        self.view.label2.setText(f'I am going to close in {self.duration} seconds.')
        self.msg.setText(f'I am going to close in {self.duration - 2} seconds.')
        self.duration -= 1

        box_dur = self.duration - 2
        if box_dur < 0:
            self.msg.close()

        if self.duration < 0:
            self.timer.stop()
            self.view.label2.hide()
            self.duration = 5

    def hideit(self, arg):
        arg.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = Controller(View())

    timecode = TimeCode()
    timecode.start_read_ltc()
    controller.view.show()
    sys.exit(app.exec())
