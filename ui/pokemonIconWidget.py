import sys
from enum import Enum

from PySide2.QtCore import QSize
from PySide2.QtWidgets import QLabel
from PySide2.QtGui import Qt, QImage, QPixmap

from utils.constants import CONSTANTS

class PokemonIconWidget(QLabel):
    def __init__(self, id, *args, **kwargs):
        super(PokemonIconWidget, self).__init__(*args, **kwargs)
        self.setStyleSheet("border: 1px solid grey;")
        self.setFixedSize(QSize(40, 40))
        self.setAlignment(Qt.AlignCenter)
        self.__img = QImage("./data/images/pokemon/" + str(id) + ".png")
        pixmap = QPixmap(self.__img)
        scaledPix = pixmap.scaled(self.size(), Qt.KeepAspectRatio, transformMode = Qt.SmoothTransformation)
        self.setPixmap(scaledPix)
        self.setToolTip("Empty")

    def setIcon(self, id, name):
        self.__img = QImage("./data/images/pokemon/" + str(id) + ".png")
        pixmap = QPixmap(self.__img)
        scaledPix = pixmap.scaled(self.size(), Qt.KeepAspectRatio, transformMode = Qt.SmoothTransformation)
        self.setPixmap(scaledPix)
        self.setToolTip(name.title())