import sys
from enum import Enum

from PySide2.QtWidgets import QWidget
from PySide2.QtCore import Signal, QSize
from PySide2.QtGui import (Qt, 
                           QPen,
                           QColor,
                           QPainter,
                           QPixmap,
                           QBrush)

from utils.constants import CONSTANTS

COLOR_NO_MAP = QColor(45,63,81)
COLOR_WALKABLE = QColor('#8aae92')
COLOR_WATER = QColor('#beebe9')
COLOR_BLOCKED = QColor('#6e5773')
COLOR_GRASS = QColor('#8aae92')
COLOR_LEDGE = QColor('#616161')
COLOR_CUT_TREE = QColor('#c06c84')
COLOR_NPC = QColor('#f3c623')
COLOR_EXIT = QColor('#81f5ff')

class MapTileWidget(QWidget):
    select = Signal(int, int, bool)
    walk = Signal(int, int)

    def __init__(self, x, y, type, tile_size, *args, **kwargs):
        super(MapTileWidget, self).__init__(*args, **kwargs)

        self.setFixedSize(QSize(tile_size, tile_size))

        self.x = x
        self.y = y
        self.clickMode = "select"
        self.type = type
        self.location = "outside"
        self.player = False
        self.playerDirection = "down"
        self.selected = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rectangle = event.rect()

        # Default colors for inner are and outer border
        outer, inner = Qt.white, Qt.lightGray

        # Figure out which tile this is and assign the color
        if self.type == TileTypeEnum.NO_MAP.value:
            inner = COLOR_NO_MAP
        elif self.type == TileTypeEnum.WALKABLE.value:
            inner = COLOR_WALKABLE
        elif self.type == TileTypeEnum.BLOCKED.value:
            inner = COLOR_BLOCKED
        elif self.type == TileTypeEnum.WATER.value:
            inner = COLOR_WATER
        elif self.type == TileTypeEnum.GRASS.value:
            inner = COLOR_GRASS
        elif self.type == TileTypeEnum.LEDGE_DOWN.value:
            inner = COLOR_LEDGE
        elif self.type == TileTypeEnum.LEDGE_LEFT.value:
            inner = COLOR_LEDGE
        elif self.type == TileTypeEnum.LEDGE_RIGHT.value:
            inner = COLOR_LEDGE
        elif self.type == TileTypeEnum.CUT_TREE.value:
            inner = COLOR_CUT_TREE
        elif self.type == TileTypeEnum.NPC.value:
            inner = COLOR_NPC
        elif self.type == TileTypeEnum.EXIT.value:
            inner = COLOR_EXIT

        pen = QPen(outer)
        pen.setWidth(0)
        painter.setPen(Qt.NoPen)
        painter.fillRect(rectangle, QBrush(inner))
        if self.type != TileTypeEnum.NO_MAP.value:
            if self.location == "indoors":
                painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_INDOOR_FLOOR))
                if self.type == TileTypeEnum.BLOCKED.value:
                    painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_INDOOR_BLOCK))
            elif self.location == "outside":
                painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_SHORT_GRASS))
                if self.type == TileTypeEnum.BLOCKED.value:
                    painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_OUTSIDE_BLOCK))
            elif self.location == "cave":
                painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_CAVE_FLOOR))
                if self.type == TileTypeEnum.BLOCKED.value:
                    painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_CAVE_BLOCK))

        if self.type == TileTypeEnum.WATER.value:
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_WATER))
        elif self.type == TileTypeEnum.GRASS.value and self.location == "outside":
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_GRASS))
        elif self.type == TileTypeEnum.EXIT.value:
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_EXIT))
        elif self.type == TileTypeEnum.CUT_TREE.value:
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_CUT_TREE))
        elif self.type == TileTypeEnum.NPC.value:
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_NPC))
        elif self.type == TileTypeEnum.LEDGE_DOWN.value:
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_LEDGE_DOWN))
        elif self.type == TileTypeEnum.LEDGE_RIGHT.value:
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_LEDGE_RIGHT))
        elif self.type == TileTypeEnum.LEDGE_LEFT.value:
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_LEDGE_LEFT))
        elif self.type == TileTypeEnum.RED_ROCK.value:
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_ROCK_RED))
        elif self.type == TileTypeEnum.BLUE_ROCK.value:
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_ROCK_BLUE))
        elif self.type == TileTypeEnum.GREEN_ROCK.value:
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_ROCK_GREEN))
        elif self.type == TileTypeEnum.PRISM_ROCK.value:
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_ROCK_PRISM))
        elif self.type == TileTypeEnum.PALE_ROCK.value:
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_ROCK_PALE))
        elif self.type == TileTypeEnum.DARK_ROCK.value:
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_ROCK_DARK))
        elif self.type == TileTypeEnum.RAINBOW_ROCK.value:
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_ROCK_RAINBOW))
        elif self.type == TileTypeEnum.EMPTY_ROCK.value:
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_ROCK_EMPTY))

        if self.selected:
            painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_POKEBALL))
        if self.player:
            if self.playerDirection == "down":
                painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_PLAYER_DOWN))
            elif self.playerDirection == "up":
                painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_PLAYER_UP))
            elif self.playerDirection == "right":
                painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_PLAYER_RIGHT))
            elif self.playerDirection == "left":
                painter.drawPixmap(rectangle, QPixmap(CONSTANTS.IMG_PLAYER_LEFT))

        painter.drawRect(rectangle)
        painter.end()

    def setType(self, type):
        self.type = type

    def setLocation(self, location):
        self.location = location

    def setClickMode(self, mode):
        self.clickMode = mode

    def setPlayer(self, player, direction="down"):
        self.player = player
        self.playerDirection = direction

    def setCoords(self, x, y):
        self.x = x
        self.y = y

    def setSelected(self, selected):
        self.selected = selected

    def getCoordsString(self):
        return str(self.x) + "," + str(self.y)

    def click(self):
        if (self.type == TileTypeEnum.WALKABLE.value or 
            self.type == TileTypeEnum.GRASS.value or 
            self.type == TileTypeEnum.WATER.value or
            self.type == TileTypeEnum.EXIT.value or 
            self.type == TileTypeEnum.CUT_TREE.value):
            if self.clickMode == "select":
                self.selected = not self.selected
                self.select.emit(self.x, self.y, self.selected)
            else:
                self.walk.emit(self.x, self.y)
            self.update()

    def mouseReleaseEvent(self, e):
        if (e.button() == Qt.LeftButton):
            self.click()

class TileTypeEnum(Enum):
    NO_MAP = -1
    WALKABLE = 0
    BLOCKED = 1
    WATER = 2
    GRASS = 3
    LEDGE_DOWN = 4
    CUT_TREE = 6
    LEDGE_LEFT = 27
    LEDGE_RIGHT = 28
    NPC = 98
    EXIT = 99
    RED_ROCK = 100
    BLUE_ROCK = 101
    GREEN_ROCK = 102
    PRISM_ROCK = 103
    PALE_ROCK = 104
    DARK_ROCK = 105
    RAINBOW_ROCK = 106
    EMPTY_ROCK = 107