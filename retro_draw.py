#!/usr/bin/env python3

import sys
from enum import Enum
from PySide2.QtWidgets import (QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QWidget)
from PySide2.QtGui import (QIcon, QPainter, QBrush, QPen, QColor, QFont, QImage)
from PySide2.QtCore import QSize, QRect, Qt

class DrawingMode(Enum):
    DRAW = 1
    ERASE = 2

class RetroDrawWidget(QWidget):
    """
    Defines widget for displaying and handling all retro drawing.
    """
    def __init__(self, parent=None):
        super(RetroDrawWidget, self).__init__(parent)

        self.grid = QImage(1024, 768, QImage.Format_RGBA8888)
        self.grid.fill(QColor(255, 255, 255, 0))
        for y in range(0, 768):
            for x in range(0, 1024, 8 * 4):
                self.grid.setPixelColor(x, y, QColor(0, 0, 0, 32))

        for x in range(0, 1024):
            for y in range(0, 768, 8 * 4):
                self.grid.setPixelColor(x, y, QColor(0, 0, 0, 32))

        self.drawable = QImage(256, 192, QImage.Format_RGBA8888)
        self.drawable.fill(QColor(255, 255, 255, 255))

        self.setCursor(Qt.CrossCursor)

        self.drawColor = QColor(0, 0, 0, 255)
        self.eraseColor = QColor(255, 255, 255, 255)

        self.drawingEnabled = False
        self.drawMode = DrawingMode.DRAW

    def sizeHint(self):
        return QSize(1024, 768)

    def minimumSizeHint(self):
        return QSize(512, 384)

    def paintEvent(self, event):
        painter = QPainter(self)
        rectTarget = self.rect()
        rectSource = QRect(0, 0, 256, 192)
        painter.drawImage(rectTarget, self.drawable, rectSource)

        painter.drawImage(rectTarget, self.grid, rectTarget)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawMode = DrawingMode.DRAW
            self.drawing = True
        elif event.button() == Qt.RightButton:
            self.drawMode = DrawingMode.ERASE
            self.drawing = True

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
        elif event.button() == Qt.RightButton:
            self.drawing = False

    def mouseMoveEvent(self, event):
        if self.drawing:
            localPos = event.localPos()
            if localPos.x() >= 0.0 and localPos.x() < 1024.0 and \
               localPos.y() >= 0.0 and localPos.y() < 768.0:
                x = localPos.x() / 4
                y = localPos.y() / 4

                if self.drawMode == DrawingMode.DRAW:
                    self.drawable.setPixelColor(x, y, self.drawColor)
                elif self.drawMode == DrawingMode.ERASE:
                    self.drawable.setPixelColor(x, y, self.eraseColor)

                self.update(self.rect())

class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setWindowTitle("Drawing App")

        self.button_draw = QPushButton(QIcon("res/draw.ico"), "")
        self.button_erase = QPushButton(QIcon("res/eraser.ico"), "")

        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.button_draw)
        layout.addWidget(self.button_erase)
        layout.addWidget(RetroDrawWidget())

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

