#!/usr/bin/env python3

import sys
from enum import Enum
from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, \
    QLabel, QCheckBox, QButtonGroup, QGroupBox, QFileDialog, QSlider, QRadioButton
from PySide2.QtGui import QIcon, QPainter, QBrush, QPen, QColor, QFont, QImage, QPixmap, QCursor
from PySide2.QtCore import QSize, QRect, QPoint, Qt, Slot
from retmod.zxbuffer import ZXSpectrumBuffer, ZXAttribute
from retmod.palette import PaletteSelectorLayout

class DrawingMode(Enum):
    DRAW = 1
    ERASE = 2
    GUIDE = 3

class MouseButton(Enum):
    NONE = 0,
    LEFT = 1,
    RIGHT = 2
    
class RetroDrawWidget(QWidget):
    """
    Defines widget for displaying and handling all retro drawing.
    """
    def __init__(self, fgIndex, bgIndex, palette, parent=None):
        super(RetroDrawWidget, self).__init__(parent)

        self.canvasSize = QSize(256, 192)
        self.canvasCenter = QPoint(self.canvasSize.width() / 2, self.canvasSize.height() / 2)
        self.fgIndex = fgIndex
        self.bgIndex = bgIndex
        self.palette = palette

        self.scale = 4
        self.screenSize = self.canvasSize * self.scale
        self.screenCenter = self.canvasCenter * self.scale

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
        self._guideCoords = QPoint(0, 0)
        self._guideZoom = 1.0
        
        self.drawable = ZXSpectrumBuffer()

        self.setCursor(Qt.CrossCursor)

        self._mouseLastPos = QCursor.pos()
        self._mouseDelta = QPoint(0, 0)
        self._mousePressed = MouseButton.NONE
        self._drawMode = DrawingMode.DRAW

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
            guideZoom = self._guide.scaled(self._guide.width() * self._guideZoom,
                                           self._guide.height() * self._guideZoom, Qt.KeepAspectRatio)
            pos = QPoint(self._guideCoords.x() + (self.screenCenter.x() - guideZoom.width() / 2),
                         self._guideCoords.y() + (self.screenCenter.y() - guideZoom.height() / 2))
            painter.setOpacity(self._guideOpacity)
            painter.drawPixmap(pos, guideZoom)
        if self._gridEnabled:
            painter.setOpacity(self._gridOpacity)
            painter.drawImage(rectTarget, self.grid, rectTarget)

        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._mousePressed = MouseButton.LEFT
        elif event.button() == Qt.RightButton:
            self._mousePressed = MouseButton.RIGHT
            
        if self._drawMode in (DrawingMode.DRAW, DrawingMode.ERASE):
            if self._mousePressed == MouseButton.LEFT:
                self.doDraw(event.localPos(), True)
            elif self._mousePressed == MouseButton.RIGHT:
                self.doDraw(event.localPos(), False)

    def mouseReleaseEvent(self, event):
        self._mousePressed = MouseButton.NONE

    def mouseMoveEvent(self, event):
        self._mouseDelta = QCursor.pos() - self._mouseLastPos
        self._mouseLastPos = QCursor.pos()
        
        if self._drawMode in (DrawingMode.DRAW, DrawingMode.ERASE):
            if self._mousePressed == MouseButton.LEFT:
                self.doDraw(event.localPos(), True)
            elif self._mousePressed == MouseButton.RIGHT:
                self.doDraw(event.localPos(), False)
        elif self._drawMode == DrawingMode.GUIDE:
            if self._mousePressed == MouseButton.LEFT:
                self._guideCoords += self._mouseDelta
                self.update(self.rect())
                
    def wheelEvent(self, event):
        if self._mousePressed:
            if self._drawMode == DrawingMode.GUIDE:
                delta = event.pixelDelta().y() * 0.01
                if delta != 0.0:
                    self._guideZoom += delta
                    self._guideZoom = self.clamp(self._guideZoom, 0.1, 8.0)
                    self.update(self.rect())                
    
    @staticmethod
    def clamp(value, min, max):
        if value < min:
            return min
        elif value > max:
            return max
        return value
        
    def doDraw(self, localPos, setPixel):
        if localPos.x() >= 0.0 and localPos.x() < self.screenSize.width() and \
           localPos.y() >= 0.0 and localPos.y() < self.screenSize.height():
            x = localPos.x() // 4
            y = localPos.y() // 4

            if setPixel:
                self.drawable.setPixel(x, y, self.fgIndex, self.bgIndex, self.palette)
            else:
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
        
    def setMode(self, mode):
        self._drawMode = mode

class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setWindowTitle("Drawing App")

        fgIndex = 0
        bgIndex = 2
        palette = 1
        self._retroWidget = RetroDrawWidget(fgIndex, bgIndex, palette)
        self._paletteWidget = PaletteSelectorLayout(fgIndex, bgIndex, palette, self._retroWidget.setColor)

        modes = QHBoxLayout()
        # Draw mode
        draw_mode = QRadioButton("Draw Mode")
        draw_mode.setChecked(True)
        draw_mode.clicked.connect(self._setModeDraw)
        modes.addWidget(draw_mode)
        erase_mode = QRadioButton("Erase Mode")
        erase_mode.setChecked(False)
        erase_mode.clicked.connect(self._setModeErase)
        modes.addWidget(erase_mode)
        guide_mode = QRadioButton("Guide Mode")
        guide_mode.setChecked(False)
        guide_mode.clicked.connect(self._setModeGuide)
        modes.addWidget(guide_mode)

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
        layout.addLayout(modes)
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
        
    @Slot()
    def _setModeDraw(self, checked):
        self._retroWidget.setMode(DrawingMode.DRAW)    

    @Slot()
    def _setModeErase(self, checked):
        self._retroWidget.setMode(DrawingMode.ERASE)    

    @Slot()
    def _setModeGuide(self, checked):
        self._retroWidget.setMode(DrawingMode.GUIDE)    

if __name__ == "__main__":
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())

