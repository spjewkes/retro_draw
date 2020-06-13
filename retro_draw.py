#!/usr/bin/env python3

import sys
from enum import Enum
from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QCheckBox, QButtonGroup, QGroupBox
from PySide2.QtGui import QIcon, QPainter, QBrush, QPen, QColor, QFont, QImage, QPixmap
from PySide2.QtCore import QSize, QRect, QPoint, Qt, Slot
from retmod.zxbuffer import ZXSpectrumBuffer, ZXAttribute

class DrawingMode(Enum):
    DRAW = 1
    ERASE = 2

class PaletteSelectorLayout(QGroupBox):
    """
    Qt Layout class for a palette
    """
    def __init__(self, fgIndex, bgIndex, palette, informFunction, parent=None):
        super(PaletteSelectorLayout, self).__init__("Palette Selector", parent)
        
        if ZXAttribute.paletteCount() != 2:
            raise Exception("The palette selector is current designed for 2 palettes only")

        self._bright = palette
        self._fgIndex = fgIndex
        self._bgIndex = bgIndex
        self._informFunction = informFunction

        vert_layout = QVBoxLayout()
        self.setLayout(vert_layout)

        # Add check box to select brightness
        bright_select = QCheckBox("Bright")
        vert_layout.addWidget(bright_select)
        if palette == 1:
            bright_select.setChecked(True)
        bright_select.clicked.connect(self._brightSelect)

        vert_layout.addSpacing(10)

        # Foreground color checkboxes
        vert_layout.addWidget(QLabel("Foreground color:"))
        self._fg_group = QButtonGroup()
        self._fg_group.setExclusive(True)
        self._createLayout(vert_layout, self._fg_group, self._fgIndexSelect, fgIndex)

        vert_layout.addSpacing(10)

        # Background color checkboxes
        vert_layout.addWidget(QLabel("Background color:"))
        self._bg_group = QButtonGroup()
        self._bg_group.setExclusive(True)
        self._createLayout(vert_layout, self._bg_group, self._bgIndexSelect, bgIndex)

    def _createLayout(self, vert_layout, buttonGroup, clickSlot, setIndex):
        horiz_layout = QHBoxLayout()
        vert_layout.addLayout(horiz_layout)

        for index in range(0, ZXAttribute.paletteSize()):
            button = QCheckBox()
            color = QColor(*ZXAttribute.getPaletteColor(index, 1))
            button.setStyleSheet("background-color: {}".format(color.name()))

            if index == setIndex:
                button.setChecked(True)

            buttonGroup.addButton(button, index)
            horiz_layout.addWidget(button)

            button.clicked.connect(clickSlot)

    @Slot()
    def _brightSelect(self, checked):
        if not checked:
            self._bright = 0
        else:
            self._bright = 1
        self._informFunction(self.fgIndex, self.bgIndex, self.palette)

    @Slot()
    def _fgIndexSelect(self, checked):
        self._fgIndex = self._fg_group.id(self.sender())
        self._informFunction(self.fgIndex, self.bgIndex, self.palette)

    @Slot()
    def _bgIndexSelect(self, checked):
        self._bgIndex = self._bg_group.id(self.sender())
        self._informFunction(self.fgIndex, self.bgIndex, self.palette)

    @property
    def palette(self):
        return self._bright

    @property
    def fgIndex(self):
        return self._fgIndex

    @property
    def bgIndex(self):
        return self._bgIndex

class RetroDrawWidget(QWidget):
    """
    Defines widget for displaying and handling all retro drawing.
    """
    def __init__(self, fgIndex, bgIndex, palette, parent=None):
        super(RetroDrawWidget, self).__init__(parent)

        # self.setAttribute(Qt.WA_NoSystemBackground, True)
        # self.setAttribute(Qt.WA_TranslucentBackground, True)

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

        self.guide = None
        # self.guide = QPixmap("baboon.bmp")
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
        # painter.setRenderHint(QPainter.LosslessImageRendering, False)
        # painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        # painter.setRenderHint(QPainter.Qt4CompatiblePainting, True)
        rectTarget = self.rect()
        rectSource = QRect(QPoint(0, 0), self.canvasSize)
        painter.drawPixmap(rectTarget, self.drawable.qpixmap, rectSource)

        painter.setOpacity(self.guideOpacity)
        if self.guide:
             painter.drawPixmap(rectTarget, self.guide, self.guide.rect())
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

if __name__ == "__main__":
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())

