#!/usr/bin/env python3

import sys
from enum import Enum
from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QCheckBox
from PySide2.QtGui import QIcon, QPainter, QBrush, QPen, QColor, QFont, QImage, QPixmap
from PySide2.QtCore import QSize, QRect, QPoint, Qt
from retmod.zxbuffer import ZXSpectrumBuffer, ZXAttribute

class DrawingMode(Enum):
    DRAW = 1
    ERASE = 2

class RetroDrawWidget(QWidget):
    """
    Defines widget for displaying and handling all retro drawing.
    """
    def __init__(self, parent=None):
        super(RetroDrawWidget, self).__init__(parent)

        self.canvasSize = QSize(256, 192)
        self.scale = 4
        self.screenSize = self.canvasSize * self.scale
        self.guideOpacity = 0.2

        self.grid = QImage(self.screenSize, QImage.Format_RGBA8888)
        self.grid.fill(QColor(255, 255, 255, 0))
        for y in range(0, self.screenSize.height()):
            for x in range(0, self.screenSize.width(), 8 * self.scale):
                self.grid.setPixelColor(x, y, QColor(0, 0, 0, 255))

        for x in range(0, self.screenSize.width()):
            for y in range(0, self.screenSize.height(), 8 * self.scale):
                self.grid.setPixelColor(x, y, QColor(0, 0, 0, 255))

        self.guide = QPixmap("baboon.bmp")
        self.drawable = ZXSpectrumBuffer()

        self.setCursor(Qt.CrossCursor)

        self.drawingEnabled = False
        self.drawMode = DrawingMode.DRAW

    def sizeHint(self):
        return self.screenSize

    def minimumSizeHint(self):
        return self.screenSize

    def paintEvent(self, event):
        painter = QPainter(self)
        rectTarget = self.rect()
        rectSource = QRect(QPoint(0, 0), self.canvasSize)
        painter.drawPixmap(rectTarget, self.drawable.qpixmap, rectSource)

        painter.setOpacity(self.guideOpacity)
        painter.drawPixmap(rectTarget, self.guide, self.guide.rect())
        painter.drawImage(rectTarget, self.grid, rectTarget)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawMode = DrawingMode.DRAW
            self.drawing = True
            self.doDraw(event.localPos())
        elif event.button() == Qt.RightButton:
            self.drawMode = DrawingMode.ERASE
            self.drawing = True
            self.doDraw(event.localPos())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
        elif event.button() == Qt.RightButton:
            self.drawing = False

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.doDraw(event.localPos())

    def doDraw(self, localPos):
        if localPos.x() >= 0.0 and localPos.x() < self.screenSize.width() and \
           localPos.y() >= 0.0 and localPos.y() < self.screenSize.height():
            x = localPos.x() // 4
            y = localPos.y() // 4

            if self.drawMode == DrawingMode.DRAW:
                self.drawable.setPixel(x, y, 0, 2, 0)
            elif self.drawMode == DrawingMode.ERASE:
                self.drawable.erasePixel(x, y, 0, 2, 0)

            self.update(self.rect())

class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setWindowTitle("Drawing App")

        self.button_draw = QPushButton(QIcon("res/draw.ico"), "")
        self.button_erase = QPushButton(QIcon("res/eraser.ico"), "")

        # Create layout and add widgets
        palette_layout = QHBoxLayout()
        palette_layout.addWidget(QLabel("Foreground color:"))
        for palette in range(0, ZXAttribute.paletteCount()):
            for index in range(0, ZXAttribute.paletteSize()):
                button = QCheckBox()
                color = QColor(*ZXAttribute.getPaletteColor(index, palette))
                button.setStyleSheet("background-color: {}".format(color.name()))
                palette_layout.addWidget(button)

        layout = QVBoxLayout()
        layout.addLayout(palette_layout)
        layout.addSpacing(10)
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

