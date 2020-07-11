#!/usr/bin/env python3

import sys
import json
from enum import Enum
from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, \
    QLabel, QCheckBox, QButtonGroup, QGroupBox, QFileDialog, QSlider, QRadioButton
from PySide2.QtGui import QIcon, QPainter, QBrush, QPen, QColor, QFont, QImage, QPixmap, QCursor
from PySide2.QtCore import QSize, QRect, QPoint, Qt, Slot
from retmod.zxbuffer import ZXSpectrumBuffer, ZXAttribute
from retmod.palette import PaletteSelectorLayout

class DrawingMode(Enum):
    PEN = 1
    DOTTED = 2
    ERASE = 3
    LINE = 4
    ATTR = 5
    GUIDE = 6

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

        self._guideFilename = None
        self._guide = None
        self._guideEnabled = True
        self._guideOpacity = 0.2
        self._guideCoords = QPoint(0, 0)
        self._guideZoom = 1.0

        self._scratch = QImage(self.screenSize, QImage.Format_RGBA8888)
        self._scratch.fill(QColor(0, 0, 0, 0))
        
        self.drawable = ZXSpectrumBuffer()

        self.setCursor(Qt.CrossCursor)

        self._mouseLastPos = self.getLocalMousePos()
        self._mouseDelta = QPoint(0, 0)
        self._mousePressed = MouseButton.NONE
        self._drawMode = DrawingMode.DOTTED

        self._lineState = None

    def encodeToJSON(self):
        rdict = dict()
        rdict["fg_index"] = self.fgIndex
        rdict["bg_index"] = self.bgIndex
        rdict["palette"] = self.palette
        rdict["grid_enabled"] = self._gridEnabled
        rdict["grid_opacity"] = self._gridOpacity
        rdict["guide_filename"] = self._guideFilename
        rdict["guide_enabled"] = self._guideEnabled
        rdict["guide_opacity"] = self._guideOpacity
        rdict["guide_coords_x"] = self._guideCoords.x()
        rdict["guide_coords_y"] = self._guideCoords.y()
        rdict["guide_zoom"] = self._guideZoom
        rdict["drawable"] = self.drawable.encodeToJSON()
        return rdict
        
    def decodeFromJSON(self, json):
        self.fgIndex = json["fg_index"]
        self.bgIndex = json["bg_index"]
        self.palette = json["palette"]
        self._gridEnabled = json["grid_enabled"]
        self._gridOpacity = json["grid_opacity"]
        self._guideFilename = json["guide_filename"]
        self._guide = QPixmap(self._guideFilename)
        self._guideEnabled = json["guide_enabled"]
        self._guideOpacity = json["guide_opacity"]
        self._guideCoords.setX(json["guide_coords_x"])
        self._guideCoords.setY(json["guide_coords_y"])
        self._guideZoom = json["guide_zoom"]
        self.drawable.decodeFromJSON(json["drawable"])

    def sizeHint(self):
        return self.screenSize

    def minimumSizeHint(self):
        return self.screenSize
    
    def getLocalMousePos(self):
        return self.mapFromGlobal(QCursor.pos())

    def paintEvent(self, event):
        super(RetroDrawWidget, self).paintEvent(event)

        painter = QPainter(self)

        rectTarget = self.rect()
        rectSource = QRect(QPoint(0, 0), self.canvasSize)
        painter.drawPixmap(rectTarget, self.drawable.qpixmap, rectSource)

        if self._guide and self._guideEnabled:
            painter.setOpacity(self._guideOpacity)
            self._paintZoomedGuide(painter)
        if self._gridEnabled:
            painter.setOpacity(self._gridOpacity)
            painter.drawImage(rectTarget, self.grid, rectTarget)

        painter.setOpacity(1.0)
        painter.drawImage(rectTarget, self._scratch, rectTarget)

        painter.end()

    def mousePressEvent(self, event):
        self._mouseLastPos = self.getLocalMousePos()
        
        if event.button() == Qt.LeftButton:
            self._mousePressed = MouseButton.LEFT
        elif event.button() == Qt.RightButton:
            self._mousePressed = MouseButton.RIGHT
            
        if self._drawMode == DrawingMode.PEN:
            if self._mousePressed == MouseButton.LEFT:
                self.doDraw(event.localPos(), True)
        
        elif self._drawMode == DrawingMode.DOTTED:
            if self._mousePressed == MouseButton.LEFT:
                self.doDraw(event.localPos(), True)
            elif self._mousePressed == MouseButton.RIGHT:
                self.doDraw(event.localPos(), False)
                
        elif self._drawMode == DrawingMode.ERASE:
            if self._mousePressed == MouseButton.LEFT:
                self.doDraw(event.localPos(), False)
                
        elif self._drawMode == DrawingMode.LINE:
            if self._mousePressed == MouseButton.LEFT:
                self._lineState = [event.localPos(), event.localPos()]
                painter = QPainter(self._scratch)
                painter.setPen(Qt.black)
                painter.drawLine(self._lineState[0], self._lineState[1])
                painter.end()
                self.update(self.rect())
                
        elif self._drawMode == DrawingMode.ATTR:
            if self._mousePressed == MouseButton.LEFT:
                self.doDrawAttr(event.localPos())

    def mouseReleaseEvent(self, event):
        if self._drawMode == DrawingMode.LINE:
            if self._mousePressed == MouseButton.LEFT and self._lineState:
                self._lineState[1] = event.localPos()
                painter = QPainter(self._scratch)
                painter.setPen(Qt.black)
                painter.drawLine(self._lineState[0], self._lineState[1])
                
                self.doDrawLine(self._lineState[0], self._lineState[1])

                painter.end()
                self._lineState = None
                self._scratch.fill(QColor(0, 0, 0, 0))
                self.update(self.rect())

        self._mousePressed = MouseButton.NONE

    def mouseMoveEvent(self, event):
        oldMousePos = self._mouseLastPos
        newMousePos = self.getLocalMousePos()
        self._mouseDelta = newMousePos - self._mouseLastPos
        self._mouseLastPos = newMousePos
        
        if self._drawMode == DrawingMode.PEN:
            if self._mousePressed == MouseButton.LEFT:
                self.doDrawLine(oldMousePos, newMousePos)
        
        if self._drawMode == DrawingMode.DOTTED:
            if self._mousePressed == MouseButton.LEFT:
                self.doDraw(newMousePos, True)
            elif self._mousePressed == MouseButton.RIGHT:
                self.doDraw(newMousePos, False)
        
        elif self._drawMode == DrawingMode.ERASE:
            if self._mousePressed == MouseButton.LEFT:
                self.doDraw(newMousePos, False)
                
        elif self._drawMode == DrawingMode.GUIDE:
            if self._mousePressed == MouseButton.LEFT:
                self._guideCoords += self._mouseDelta
                self.update(self.rect())
                
        elif self._drawMode == DrawingMode.LINE:
            if self._mousePressed == MouseButton.LEFT and self._lineState:
                painter = QPainter(self._scratch)
                self._scratch.fill(QColor(0, 0, 0, 0))
                painter.setPen(Qt.black)
                self._lineState[1] = event.localPos()
                painter.drawLine(self._lineState[0], self._lineState[1])
                painter.end()
                self.update(self.rect())
               
        elif self._drawMode == DrawingMode.ATTR:
            if self._mousePressed == MouseButton.LEFT:
                self.doDrawAttr(event.localPos())

                
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
        x = localPos.x() // self.scale
        y = localPos.y() // self.scale

        if setPixel:
            self.drawable.setPixel(x, y, self.fgIndex, self.bgIndex, self.palette)
        else:
            self.drawable.erasePixel(x, y, self.fgIndex, self.bgIndex, self.palette)

        self.update(self.rect())

    def doDrawAttr(self, localPos):
        x = localPos.x() // self.scale
        y = localPos.y() // self.scale
        
        self.drawable.setAttr(x, y, self.fgIndex, self.bgIndex, self.palette)
        self.update(self.rect())
            
    def doDrawLine(self, localStartPos, localEndPos):
        x1 = localStartPos.x() // self.scale
        y1 = localStartPos.y() // self.scale
        x2 = localEndPos.x() // self.scale
        y2 = localEndPos.y() // self.scale
        self.drawable.drawLine(x1, y1, x2, y2, self.fgIndex, self.bgIndex, self.palette)
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
        self._guideFilename = filename
        self._guide = QPixmap(self._guideFilename)
        self.repaint()
        
    def setGuide(self, checked):
        self._guideEnabled = checked
        self.repaint()

    def setGuideOpacity(self, value):
        self._guideOpacity = value / 100.0
        self.repaint()
        
    def setMode(self, mode):
        self._drawMode = mode
        
    def clear(self):
        self.drawable.clear(self.fgIndex, self.bgIndex, self.palette)
        self.repaint()

    def _paintZoomedGuide(self, painter):
        guideZoom = self._guide.scaled(self._guide.width() * self._guideZoom,
                                       self._guide.height() * self._guideZoom, Qt.KeepAspectRatio)
        pos = QPoint(self._guideCoords.x() + (self.screenCenter.x() - guideZoom.width() / 2),
                     self._guideCoords.y() + (self.screenCenter.y() - guideZoom.height() / 2))
        painter.drawPixmap(pos, guideZoom)
        
    def copyGuide(self):
        # This isn't the most efficient way to do this but it just needs to be
        # reasonably fast
        self.drawable.clear(self.fgIndex, self.bgIndex, self.palette)

        guide_copy = QImage(self.screenSize, QImage.Format_RGBA8888)
        guide_copy.fill(QColor("white"))

        painter = QPainter(guide_copy)
        self._paintZoomedGuide(painter)
        
        shrunk_guide = guide_copy.smoothScaled(self.canvasSize.width(), self.canvasSize.height())
        mono_guide = shrunk_guide.convertToFormat(QImage.Format_Mono)
        
        for x in range(0, self.canvasSize.width()):
            for y in range(0, self.canvasSize.height()):
                if mono_guide.pixel(x, y) == QColor("black"):
                      self.drawable.setPixel(x, y, self.fgIndex, self.bgIndex, self.palette)      

        painter.end()
        self.repaint()

class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setWindowTitle("Drawing App")

        fgIndex = 0
        bgIndex = 7
        palette = 0
        self._retroWidget = RetroDrawWidget(fgIndex, bgIndex, palette)
        self._paletteWidget = PaletteSelectorLayout(fgIndex, bgIndex, palette, self._retroWidget.setColor)

        modes = QHBoxLayout()
        # Pen mode
        pen_mode = QRadioButton("Pen Mode")
        pen_mode.setChecked(False)
        pen_mode.clicked.connect(lambda: self._retroWidget.setMode(DrawingMode.PEN))
        modes.addWidget(pen_mode)
        # Dotted mode
        dotted_mode = QRadioButton("Dotted Mode")
        dotted_mode.setChecked(True)
        dotted_mode.clicked.connect(lambda: self._retroWidget.setMode(DrawingMode.DOTTED))
        modes.addWidget(dotted_mode)
        # Erase mode
        erase_mode = QRadioButton("Erase Mode")
        erase_mode.setChecked(False)
        erase_mode.clicked.connect(lambda: self._retroWidget.setMode(DrawingMode.ERASE))
        modes.addWidget(erase_mode)
        # Line mode
        line_mode = QRadioButton("Line Mode")
        line_mode.setChecked(False)
        line_mode.clicked.connect(lambda: self._retroWidget.setMode(DrawingMode.LINE))
        modes.addWidget(line_mode)
        # Attr mode
        attr_mode = QRadioButton("Attr Mode")
        attr_mode.setChecked(False)
        attr_mode.clicked.connect(lambda: self._retroWidget.setMode(DrawingMode.ATTR))
        modes.addWidget(attr_mode)
        # Guide mode
        guide_mode = QRadioButton("Guide Mode")
        guide_mode.setChecked(False)
        guide_mode.clicked.connect(lambda: self._retroWidget.setMode(DrawingMode.GUIDE))
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
        # Clear screen
        clear_screen_button = QPushButton("Clear Screen")
        clear_screen_button.clicked.connect(self._clearScreen)
        buttons.addWidget(clear_screen_button)        
        # Copy Guide
        copy_guide_button = QPushButton("Copy Guide")
        copy_guide_button.clicked.connect(self._copyGuide)
        buttons.addWidget(copy_guide_button)
        # Save Project
        save_project_button = QPushButton("Save Project")
        save_project_button.clicked.connect(self._saveProject)
        buttons.addWidget(save_project_button)
        # Load Project
        load_project_button = QPushButton("Load Project")
        load_project_button.clicked.connect(self._loadProject)
        buttons.addWidget(load_project_button)
                
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
    def _clearScreen(self):
        self._retroWidget.clear()
        
    @Slot()
    def _copyGuide(self):
        self._retroWidget.copyGuide()
        
    @Slot()
    def _saveProject(self):
        with open("test_proj.json", "w") as output:
            json.dump(self._retroWidget.encodeToJSON(), output)
            
    @Slot()
    def _loadProject(self):
        with open("test_proj.json", "r") as input:
            self._retroWidget.decodeFromJSON(json.load(input))
        self._retroWidget.repaint()

if __name__ == "__main__":
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())

