#!/usr/bin/env python3

import sys
from enum import Enum
from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, \
    QLabel, QCheckBox, QButtonGroup, QGroupBox, QFileDialog
from PySide2.QtGui import QIcon, QPainter, QBrush, QPen, QColor, QFont, QImage, QPixmap
from PySide2.QtCore import QSize, QRect, QPoint, Qt, Slot
from retmod.zxbuffer import ZXSpectrumBuffer, ZXAttribute
from retmod.palette import PaletteSelectorLayout

class DrawingMode(Enum):
    DRAW = 1
    ERASE = 2

class RetroDrawWidget(QWidget):
    """
    Defines widget for displaying and handling all retro drawing.
    """
    def __init__(self, fgIndex, bgIndex, palette, parent=None):
        super(RetroDrawWidget, self).__init__(parent)

        self.canvasSize = QSize(256, 192)
        self.fgIndex = fgIndex
        self.bgIndex = bgIndex
        self.palette = palette

        self.scale = 4
        self.screenSize = self.canvasSize * self.scale
        self.guideOpacity = 0.2

        self.grid = QImage(self.screenSize, QImage.Format_RGBA8888)
        self.grid.fill(QColor(0, 0, 0, 0))
        for y in range(0, self.screenSize.height()):
            for x in range(0, self.screenSize.width(), 8 * self.scale):
                self.grid.setPixelColor(x, y, QColor(0, 0, 0, 255))

        for x in range(0, self.screenSize.width()):
            for y in range(0, self.screenSize.height(), 8 * self.scale):
                self.grid.setPixelColor(x, y, QColor(0, 0, 0, 255))

        self._guide = None
        self.drawable = ZXSpectrumBuffer()

        self.setCursor(Qt.CrossCursor)

        self.drawingEnabled = False
        self.drawMode = DrawingMode.DRAW

    def sizeHint(self):
        return self.screenSize

    def minimumSizeHint(self):
        return self.screenSize

    def paintEvent(self, event):
        super(RetroDrawWidget, self).paintEvent(event)

        painter = QPainter(self)

        rectTarget = self.rect()
        rectSource = QRect(QPoint(0, 0), self.canvasSize)
        painter.drawPixmap(rectTarget, self.drawable.qpixmap, rectSource)

        painter.setOpacity(self.guideOpacity)
        if self._guide:
             painter.drawPixmap(rectTarget, self._guide, self._guide.rect())
        painter.drawImage(rectTarget, self.grid, rectTarget)

        painter.end()

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
                self.drawable.setPixel(x, y, self.fgIndex, self.bgIndex, self.palette)
            elif self.drawMode == DrawingMode.ERASE:
                self.drawable.erasePixel(x, y, self.fgIndex, self.bgIndex, self.palette)

            self.update(self.rect())

    def setColor(self, fgIndex, bgIndex, palette):
        self.fgIndex = fgIndex
        self.bgIndex = bgIndex
        self.palette = palette
        
    def saveImage(self, filename, format=None):
        self.drawable.saveBuffer(filename)
        
    def setGuide(self, filename):
        self._guide = QPixmap(filename)
        self.repaint()

class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setWindowTitle("Drawing App")

        fgIndex = 0
        bgIndex = 2
        palette = 1
        self._retroWidget = RetroDrawWidget(fgIndex, bgIndex, palette)
        self._paletteWidget = PaletteSelectorLayout(fgIndex, bgIndex, palette, self._retroWidget.setColor)

        buttons = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self._saveImage)
        buttons.addWidget(save_button)
        load_guide_button = QPushButton("Load guide")
        load_guide_button.clicked.connect(self._setGuide)
        buttons.addWidget(load_guide_button)        

        layout = QVBoxLayout()
        layout.addLayout(buttons)
        layout.addSpacing(10)
        layout.addWidget(self._paletteWidget)
        layout.addSpacing(10)
        layout.addWidget(self._retroWidget)

        # Set dialog layout
        self.setLayout(layout)
        
    @Slot()
    def _saveImage(self):
        self._retroWidget.saveImage("output.png")
        
    @Slot()
    def _setGuide(self):
        filename = QFileDialog.getOpenFileName(self, "Choose guide image", ".", "Image Files (*.png *.jpg *.bmp)")
        if filename[0]:
            self._retroWidget.setGuide(filename[0])

if __name__ == "__main__":
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())

