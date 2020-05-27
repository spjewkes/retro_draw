#!/usr/bin/env python3

import sys
from PySide2.QtWidgets import (QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QWidget)
from PySide2.QtGui import (QIcon, QPainter, QBrush, QPen, QColor, QFont, QImage)
from PySide2.QtCore import QSize, QRect, Qt

class RenderArea(QWidget):
    def __init__(self, parent=None):
        super(RenderArea, self).__init__(parent)

        self.drawable = QImage(256, 192, QImage.Format_RGBA8888)
        self.drawable.fill(QColor(255, 255, 255, 255))

        self.drawing = False
        self.setCursor(Qt.CrossCursor)

    def sizeHint(self):
        return QSize(1024, 768)

    def minimumSizeHint(self):
        return QSize(512, 384)

    def paintEvent(self, event):
        painter = QPainter(self)
        rectTarget = self.rect()
        rectSource = QRect(0, 0, 256, 192)
        painter.drawImage(rectTarget, self.drawable, rectSource)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    def mouseMoveEvent(self, event):
        if self.drawing:
            localPos = event.localPos()
            if localPos.x() >= 0.0 and localPos.x() < 1024.0 and \
               localPos.y() >= 0.0 and localPos.y() < 768.0:
                self.drawable.setPixelColor(localPos.x() / 4, localPos.y() / 4, QColor(0, 0, 0, 255))

                self.update(self.rect())

class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setWindowTitle("Drawing App")

        self.button_draw = QPushButton(QIcon("draw.ico"), "")
        self.button_erase = QPushButton(QIcon("eraser.ico"), "")

        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.button_draw)
        layout.addWidget(self.button_erase)
        layout.addWidget(RenderArea())

        # Set dialog layout
        self.setLayout(layout)

        self.button_draw.clicked.connect(self.drawMode)
        self.button_erase.clicked.connect(self.eraseMode)

        self.mode = None

    def drawMode(self):
        self.mode = "draw"

    def eraseMode(self):
        self.mode = "erase"

if __name__ == "__main__":
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())

