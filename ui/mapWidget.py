import sys
import time

from PySide2.QtWidgets import QWidget, QGridLayout, QDesktopWidget, QHBoxLayout
from PySide2.QtCore import Signal, QEvent, Qt
from math import ceil

from ui.mapTileWidget import MapTileWidget, TileTypeEnum
from utils.constants import CONSTANTS
from utils.mapManager import MapManager
from utils.pathfinding import *

class MapWidget(QWidget):
	walkCommandSignal = Signal(object)
	def __init__(self, parent):
		super(MapWidget, self).__init__(parent)

		self.__contentLayout = QHBoxLayout()
		self.__contentLayout.setSpacing(0)
		self.__contentLayout.setMargin(0)

		# Holds the map grid
		self.__boardContainer = QWidget()
		self.__leftSpace = QWidget()
		self.__rightSpace = QWidget()

		self.__contentLayout.addWidget(self.__leftSpace)
		self.__contentLayout.addWidget(self.__boardContainer)
		self.__contentLayout.addWidget(self.__rightSpace)

		# Create new grid with no spacing
		self.__grid = QGridLayout()
		self.__grid.setSpacing(0)
		self.__grid.setMargin(2)
		self.__boardContainer.setLayout(self.__grid)

		# Apply the new grid
		self.setLayout(self.__contentLayout)

		self.__playerX = 0
		self.__playerY = 0
		self.__direction = "down"
		self.__playerMount = ""
		self.__mapWidth = 0
		self.__mapHeight = 0
		self.__mapName = None
		self.__tiles = []
		self.__selected = dict()

		screen_resolution = QDesktopWidget().screenGeometry(-1)
		self.tileSize = int((screen_resolution.height() / 1.85) / CONSTANTS.WIDGET_MAP_VIEW_HEIGHT)
		self.horizontalTiles = CONSTANTS.WIDGET_MAP_VIEW_WIDTH

		self.__mapManager = MapManager()
		self.__mapCollisions = [[]]
		self.initTiles()

	def initTiles(self):
		for x in range(0, self.horizontalTiles):
			self.__tiles.append([])
			for y in range(0, CONSTANTS.WIDGET_MAP_VIEW_HEIGHT):
				tile = MapTileWidget(x, y, -1, self.tileSize)
				tile.select.connect(self.__tileUpdated)
				tile.walk.connect(self.__walkIssued)
				self.__tiles[x].append(tile)
				self.__grid.addWidget(tile, y, x)

	def resizeGrid(self, new_tile_count):
		if new_tile_count > self.horizontalTiles:

			x = new_tile_count - (new_tile_count - len(self.__tiles))

			while len(self.__tiles) <= new_tile_count:
				self.__tiles.append([])
				for y in range(0, CONSTANTS.WIDGET_MAP_VIEW_HEIGHT):
					tile = MapTileWidget(x, y, -1, self.tileSize)
					tile.select.connect(self.__tileUpdated)
					tile.walk.connect(self.__walkIssued)
					self.__tiles[x].append(tile)
					self.__grid.addWidget(tile, y, x)
				x += 1
		elif new_tile_count < self.horizontalTiles:
			x = new_tile_count
			while len(self.__tiles) > new_tile_count:
				tile_column = self.__tiles.pop()
				for atile in tile_column:
					self.__grid.removeWidget(atile)
					atile.deleteLater()
					del atile

		self.horizontalTiles = new_tile_count

	def resizeEvent(self, event):

		# We want to give some space for when we're downsizing.
		width_px = self.geometry().width() - 80
		new_tile_count = ceil((width_px) / self.tileSize)
		# New size is different than previous size
		if new_tile_count != self.horizontalTiles:
			# Only resize if value is above minimum and odd, to better position the player in center.
			if new_tile_count >= CONSTANTS.WIDGET_MAP_VIEW_WIDTH:
				self.resizeGrid(new_tile_count)
				# Make sure player is logged in to draw map
				if self.__playerX != 0 and self.__playerY != 0:
					self.drawMap()

	def __changeMap(self, mapName, timeout):
		if self.__mapManager.map(mapName) is not None:
			self.__mapName = mapName
			self.__mapCollisions = self.__mapManager.map(mapName)
			if not timeout:
				self.__selected.clear()
			self.__mapWidth = self.__mapManager.width(mapName)
			self.__mapHeight = self.__mapManager.height(mapName)
			return True
		else:
			return False
	def addRocks(self, rocks):
		self.__mapManager.addRocks(rocks)
		self.__mapCollisions = self.__mapManager.collision
		self.drawMap()

	def updatePosition(self, map, x, y, direction, timeout):
		self.__direction = direction
		if map == "" and x == 0 and y == 0:
			self.__playerX = 0
			self.__playerY = 0
			self.__mapWidth = 0
			self.__mapHeight = 0
			self.__mapName = None
			self.__tiles = []
			if not timeout:
				self.__selected = dict()
			self.__mapCollisions = [[]]
			self.initTiles()
		else:
			if map != self.__mapName:
				self.__changeMap(map, timeout)
			self.__playerX = x
			self.__playerY = y
			self.drawMap()

	def __walkIssued(self, x, y):
		surf = self.__playerMount == "surf"
		path = astar(self.__mapCollisions, (self.__playerY, self.__playerX), (y,x), surf)
		if path is  not None:
			path.pop(0)
			self.walkCommandSignal.emit(path)

	def __tileUpdated(self, x, y, selected):
		coordKey = str(x) + "," + str(y)

		if coordKey in self.__selected:
			if not selected:
				self.__selected.pop(coordKey)
		else:
			self.__selected[coordKey] = True

	def setClickMode(self, mode):
		for x in range(0, self.horizontalTiles):
			for y in range(0, CONSTANTS.WIDGET_MAP_VIEW_HEIGHT):
				self.__tiles[x][y].setClickMode(mode)

	def setMount(self, mount):
		self.__playerMount = mount

	def drawMap(self):
		widthCenter = int(self.horizontalTiles/2)
		heightCenter = int(CONSTANTS.WIDGET_MAP_VIEW_HEIGHT/2)

		for x in range(0, self.horizontalTiles):
			for y in range(0, CONSTANTS.WIDGET_MAP_VIEW_HEIGHT):
				offsetX = 0
				offsetY = 0

				if(x == widthCenter and y == heightCenter):
					self.__tiles[x][y].setPlayer(True, self.__direction)
				else:
					self.__tiles[x][y].setPlayer(False)

				if x < widthCenter:
					offsetX = -(widthCenter - x)
				else:
					offsetX = x - widthCenter

				if y < heightCenter:
					offsetY = -(heightCenter - y)
				else:
					offsetY = y - heightCenter

				trueX = self.__playerX + offsetX
				trueY = self.__playerY + offsetY

				if ((trueX < 0) or (trueX > self.__mapWidth) or 
				    (trueY < 0) or (trueY > self.__mapHeight)):
					self.__tiles[x][y].setType(TileTypeEnum.NO_MAP.value)
					self.__tiles[x][y].setCoords(-1, -1)
					self.__tiles[x][y].setSelected(False)
				else:
					tile_type = self.__mapCollisions[trueY][trueX]

					for exit in self.__mapManager.exits:
						if exit[0] == trueX and exit[1] == trueY:
							tile_type = TileTypeEnum.EXIT.value
							
					self.__tiles[x][y].setType(tile_type)
					self.__tiles[x][y].setLocation(self.__mapManager.location)
					self.__tiles[x][y].setCoords(trueX, trueY)
					if self.__tiles[x][y].getCoordsString() in self.__selected:
						self.__tiles[x][y].setSelected(True)
					else:
						self.__tiles[x][y].setSelected(False)

		self.update()


	def getSelectedTiles(self):
		return self.__selected