from PySide2 import QtGui
from PySide2.QtGui import QColor, QPixmap
from PySide2.QtCore import QSize
from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt

class ZXAttribute(object):
    """
    Defines the state of a ZX Spectrum attribute
    """
    def __init__(self, ink=0, paper=0, palette=0):
        self._ink = ink
        self._paper = paper
        self._palette = palette

    @staticmethod
    def paletteCount():
        return 2

    @staticmethod
    def paletteSize(paletteIndex=0):
        return 8

    @staticmethod
    def getPaletteColor(indexColor, indexPalette):
        palette = ((0, 0, 0), (0, 0, 215), (215, 0, 0), (215, 0, 215),
                   (0, 215, 0), (0, 215, 215), (215, 215, 0), (215, 215, 215))
        brightPalette = ((0, 0, 0), (0, 0, 255), (255, 0, 0), (255, 0, 255),
                         (0, 255, 0), (0, 255, 255), (255, 255, 0), (255, 255, 255))

        if indexPalette == 0:
            return palette[indexColor]
        
        return brightPalette[indexColor]

    @staticmethod
    def _validatePaletteColor(indexColor, indexPalette=0):
        if indexColor < 0 or indexColor >= ZXAttribute.paletteSize():
            raise IndexError("Index color {} is out of bounds (palette size {})".
                             format(indexColor, ZXAttribute.paletteSize()))
        if indexPalette < 0 or indexPalette >= ZXAttribute.paletteCount():
            raise IndexError("Index palette {} is out of bounds (palette count {})".
                             format(indexPalette, ZXAttribute.paletteCount()))

    @property
    def ink(self):
        return self._ink

    @ink.setter
    def ink(self, value):
        ZXAttribute._validatePaletteColor(value)
        self._ink = value

    @property
    def paper(self):
        return self._paper

    @paper.setter
    def paper(self, value):
        ZXAttribute._validatePaletteColor(value)
        self._paper = value

    @property
    def palette(self):
        return self._palette

    @palette.setter
    def palette(self, value):
        ZXAttribute._validatePaletteColor(self._ink, value)
        self._palette = value

class ZXSpectrumBuffer(object):
    """
    This class defines a buffer for the ZX Spectrum.
    """
    def __init__(self, fgIndex=0, bgIndex=7, paletteIndex=0):
        self._paper = Image.new("RGB", self.size.toTuple())
        self._ink = Image.new("RGB", self.size.toTuple())
        self._mask = Image.new("1", self.size.toTuple())
        self._final = None
        self._needsUpdate = True

        # Set up attribute colors
        self._attributes = dict()
        for y in range(0, self.sizeAttr.height()):
            for x in range(0, self.sizeAttr.width()):
                self._attributes[(x, y)] = ZXAttribute()

        self.clear(fgIndex, bgIndex, paletteIndex)
        
    def _update(self):
        if self._needsUpdate:
            self._final = ImageQt(Image.composite(self._ink, self._paper, self._mask))
            self._needsUpdate = False

    @property
    def size(self):
        return QSize(256, 192)

    @property
    def sizeAttr(self):
        return QSize(32, 24)
    
    @property
    def qpixmap(self):
        self._update()
        return QtGui.QPixmap.fromImage(self._final)

    def clear(self, fgIndex, bgIndex, paletteIndex=0):
        for y in range(0, self.sizeAttr.height()):
            for x in range(0, self.sizeAttr.width()):
                self._attributes[(x, y)].ink = fgIndex
                self._attributes[(x, y)].paper = bgIndex
                self._attributes[(x, y)].palette = paletteIndex
        
        im_ink = ImageDraw.Draw(self._ink)
        im_ink.rectangle([0, 0, self.size.width() - 1, self.size.height() - 1],
                         fill=ZXAttribute.getPaletteColor(fgIndex, paletteIndex))

        im_paper = ImageDraw.Draw(self._paper)
        im_paper.rectangle([0, 0, self.size.width() - 1, self.size.height() - 1],
                           fill=ZXAttribute.getPaletteColor(bgIndex, paletteIndex))

        im_mask = ImageDraw.Draw(self._mask)
        im_mask.rectangle([0, 0, self.size.width() - 1, self.size.height() - 1],
                          fill=0)

        self._needsUpdate = True

    def setAttr(self, x, y, fgIndex, bgIndex, paletteIndex):
        pos = (x * 8, y * 8)

        # This does not validate for speed purposes

        attr = self._attributes[(x, y)]

        paletteChanged = False
        if attr.palette != paletteIndex:
            paletteChanged = True
            attr.palette = paletteIndex

        if attr.ink != fgIndex or paletteChanged:
            attr.ink = fgIndex
            im_ink = ImageDraw.Draw(self._ink)
            im_ink.rectangle([pos[0], pos[1], pos[0]+7, pos[1]+7],
                             fill=ZXAttribute.getPaletteColor(fgIndex, paletteIndex))
            self._needsUpdate = True

        if attr.paper != bgIndex or paletteChanged:
            attr.paper = bgIndex
            im_paper = ImageDraw.Draw(self._paper)
            im_paper.rectangle([pos[0], pos[1], pos[0]+7, pos[1]+7],
                               fill=ZXAttribute.getPaletteColor(bgIndex, paletteIndex))
            self._needsUpdate = True

    def setPixel(self, x, y, fgIndex, bgIndex, paletteIndex):
        self.setAttr(x // 8, y // 8, fgIndex, bgIndex, paletteIndex)
        self._mask.putpixel((int(x), int(y)), 1)
        self._needsUpdate = True

    def erasePixel(self, x, y, fgIndex, bgIndex, paletteIndex):
        self.setAttr(x // 8, y // 8, fgIndex, bgIndex, paletteIndex)
        self._mask.putpixel((int(x), int(y)), 0)
        self._needsUpdate = True
        
    def saveBuffer(self, filename, format=None):
        self._update()
        self._final.save(filename, format)
