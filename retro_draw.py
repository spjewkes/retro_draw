#!/usr/bin/env python3

import sys
from enum import Enum
from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, \
    QLabel, QCheckBox, QButtonGroup, QGroupBox, QFileDialog, QSlider
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

        self.grid = QImage(self.screenSize, QImage.Format_RGBA8888)
        self.grid.fill(QColor(0, 0, 0, 0))
        for y in range(0, self.screenSize.height()):
            for x in range(0, self.screenSize.width(), 8 * self.scale):
                self.grid.setPixelColor(x, y, QColor(0, 0, 0, 255))

        for x in range(0, self.screenSize.width()):
            for y in range(0, self.screenSize.height(), 8 * self.scale):
                self.grid.setPixelColor(x, y, QColor(0, 0, 0, 255))
        self._gridEnabled = True
        self._gridOpacity = 0.2

        self._guide = None
        self._guideEnabled = True
        self._guideOpacity = 0.2
        
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

        if self._guide and self._guideEnabled:
            painter.setOpacity(self._guideOpacity)
            painter.drawPixmap(rectTarget, self._guide, self._guide.rect())
        if self._gridEnabled:
            painter.setOpacity(self._gridOpacity)
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
        
    def setGrid(self, checked):
        self._gridEnabled = checked
        self.repaint()
        
    def setGridOpacity(self, value):
        self._gridOpacity = value / 100.0
        self.repaint()
        
    def setGuideImage(self, filename):
        self._guide = QPixmap(filename)
        self.repaint()
        
    def setGuide(self, checked):
        self._guideEnabled = checked
        self.repaint()

    def setGuideOpacity(self, value):
        self._guideOpacity = value / 100.0
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
        # Save image button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self._saveImage)
        buttons.addWidget(save_button)
        # Load guide image button
        load_guide_button = QPushButton("Load guide")
        load_guide_button.clicked.connect(self._setGuideImage)
        buttons.addWidget(load_guide_button) 
        # Enable guide image check box
        enable_guide_check = QCheckBox("Guide Enabled")
        enable_guide_check.setChecked(True)
        enable_guide_check.clicked.connect(self._setGuide)
        self._retroWidget.setGuide(True)
        buttons.addWidget(enable_guide_check)
        # Enable grid check box     
        enable_grid_check = QCheckBox("Grid Enabled")
        enable_grid_check.setChecked(True)
        enable_grid_check.clicked.connect(self._setGrid)
        self._retroWidget.setGrid(True)
        buttons.addWidget(enable_grid_check)
        
        sliders = QHBoxLayout()
        # Guide slider
        sliders.addWidget(QLabel("Guide Opacity:"))
        guide_slider = QSlider(Qt.Horizontal)
        guide_slider.setTickInterval(10)
        guide_slider.setTickPosition(QSlider.TicksBothSides)
        guide_slider.setSingleStep(1)
        guide_slider.valueChanged.connect(self._setGuideSlider)
        guide_slider.setValue(20)
        self._retroWidget.setGuideOpacity(20)
        sliders.addWidget(guide_slider)
        # Grid slider
        sliders.addWidget(QLabel("Grid Opacity:"))
        grid_slider = QSlider(Qt.Horizontal)
        grid_slider.setTickInterval(10)
        grid_slider.setTickPosition(QSlider.TicksBothSides)
        grid_slider.setSingleStep(1)
        grid_slider.valueChanged.connect(self._setGridSlider)
        grid_slider.setValue(20)
        self._retroWidget.setGridOpacity(20)
        sliders.addWidget(grid_slider)

        layout = QVBoxLayout()
        layout.addLayout(buttons)
        layout.addLayout(sliders)
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
    def _setGrid(self, checked):
        self._retroWidget.setGrid(checked)
        
    @Slot()
    def _setGridSlider(self, value):
        self._retroWidget.setGridOpacity(value)

    @Slot()
    def _setGuideImage(self):
        filename = QFileDialog.getOpenFileName(self, "Choose guide image", ".", "Image Files (*.png *.jpg *.bmp)")
        if filename[0]:
            self._retroWidget.setGuideImage(filename[0])
            
    @Slot()
    def _setGuide(self, checked):
        self._retroWidget.setGuide(checked)
        
    @Slot()
    def _setGuideSlider(self, value):
        self._retroWidget.setGuideOpacity(value)

if __name__ == "__main__":
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())

