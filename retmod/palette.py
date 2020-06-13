#!/usr/bin/env python3

from PySide2.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QButtonGroup, QGroupBox
from PySide2.QtGui import QColor
from PySide2.QtCore import Slot
from retmod.zxbuffer import ZXAttribute

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
