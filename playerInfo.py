import re
from pokemon import Pokemon
from utils.mapManager import MapManager

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

class PlayerInfo(QObject):
	stepsWalkedSignal = Signal()
	def __init__(self):
		super(PlayerInfo, self).__init__()
		self.__username = None
		self.money = 0
		self.credits = 0
		self.__inventory = {}
		self.__inventoryList = []
		self.__badges = []
		self.__x = 0
		self.__y = 0
		self.__map = None
		self.cleanMapName = None
		self.__creationEpoch = None
		self.characterCreated = 0
		self.__membership = None
		self.__membershipTime = 0
		self.__clan = ''
		self.fishingLevel = 0
		self.fishingExp = 0
		self.team = []
		self.mount = ''
		self.direction = 'down'
		self.moveType = ''
		self.fishing = 0
		self.moving = False
		self.battle = False
		self.stepsWalked = 0
		self.mapMovements = 0
		self.movementSpeedMod = 0
		self.movementSpeed = 0
		self.activePokemon = 0

		self.__mapManager = MapManager()
		self.mapCollisions = [[]]
		self.selectedTiles = None

	def parseData(self, rawData):
		"""Parse out the user information provided by the server.

		I hate absolutely everything about this message. It is not very
		clean and easy to parse. Much of the logic below is hardcoded
		and dirty. 
		"""

		segments = rawData.split('`')

		self.money = int(segments[4])
		self.credits = int(segments[5])

		segment_num = 6

		for segment in range(segment_num, len(segments)):
			if segments[segment] != ')()(09a0jd':
				item = segments[segment].split(',')
				self.addItemToInventory(item[0], int(item[1]))
			else:
				segment_num = segment + 1
				break

		badges = segments[segment_num].split(',')
		for badge in badges:
			self.__badges.append(badge)

		segment_num = segment_num + 1

		self.__x = int(segments[segment_num])
		segment_num = segment_num + 1

		self.__y = int(segments[segment_num])
		segment_num = segment_num + 1

		self.__map = segments[segment_num]
		self.cleanMapName = re.sub(r'\([^()]*\)', '', segments[segment_num]).strip()
		self.mapCollisions = self.__mapManager.map(self.cleanMapName)
		segment_num = segment_num + 1

		# Skip the next fields until we get to member info
		# Dirty but it needs to be done.
		for segment in range(segment_num, len(segments)):
			if segments[segment] == ')()(09a0jc':
				segment_num = segment + 1
				break

		self.__creationEpoch = int(segments[segment_num])
		segment_num = segment_num + 2

		self.characterCreated = int(segments[segment_num])
		segment_num = segment_num + 1

		self.__membership = segments[segment_num]
		segment_num = segment_num + 1

		self.__membershipTime = int(segments[segment_num])
		segment_num = segment_num + 1

		self.__clan = str(segments[segment_num]) if str(segments[segment_num]) != '0' else ""
		segment_num = segment_num + 13
		
		# Pokemon in team
		for segment in range(segment_num, len(segments)):
			if segments[segment] != ')()(09a0jb':
				pokemonString = segments[segment].replace('[', '').replace(']','')
				self.team.append(Pokemon(pokemonString))
			else:
				segment_num = segment + 1
				break

		# Move forward to )()(09a0jb tag
		for segment in range(segment_num, len(segments)):
			if segments[segment] == ')()(09a0js':
				segment_num = segment + 1
				break

		self.movementSpeedMod = 1
		if int(segments[segment_num + 9]) > 0:
			if int(segments[segment_num + 8]) == 2:
				self.movementSpeedMod = 2
			elif int(segments[segment_num + 8]) == 0.500000:
				self.movementSpeedMod = 0.500000

		self.movementSpeed = 8 * self.movementSpeedMod
		self.fishingLevel = int(segments[segment_num + 10])
		self.fishingExp = int(segments[segment_num + 11])

	def isMapExitTile(self):
		for exit in self.__mapManager.exits:
			if exit[0] == self.__x and exit[1] == self.__y:
				return True

		return False

	def getMapExit(self):
		exit_data = []
		for exit in self.__mapManager.exits:
			if exit[0] == self.__x and exit[1] == self.__y:
				exit_data.append(re.sub(r'\([^()]*\)', '', exit[2]).strip())
				exit_data.append(exit[3])
				exit_data.append(exit[4])
				break

		return exit_data

	def exitMap(self, position):

		temp_clean_map_name = re.sub(r'\([^()]*\)', '', position[0]).strip()
		temp_map_collisions = self.__mapManager.map(temp_clean_map_name)
		if temp_map_collisions is not None:
			self.__map = position[0]
			self.cleanMapName = temp_clean_map_name
			self.mapCollisions = temp_map_collisions
			self.__x = position[1]
			self.__y = position[2]
			return True
		else:
			return False

	def updateTeam(self, data):
		if data is not None:
			updatedTeam = []
			data = data.split("],")
			for member in data:
				updatedTeam.append(Pokemon(member.replace("[","").replace("]","")))
			self.team = updatedTeam

	def updateInventory(self, data):
		if data is not None:
			self.__inventory = {}
			self.__inventoryList = []
			strings = data.replace('[','').replace("]]","").split('],')
			for item in strings:
				split_item = item.split(",")
				self.addItemToInventory(split_item[0], int(split_item[1]))

	def activePokemonAlive(self):
		if len(self.team) > 0:
			return self.team[self.activePokemon].currentHealth > 1
		else:
			return False

	def setUsername(self, username):
		self.__username = username
		
	def getX(self):
		return int(self.__x)

	def getY(self):
		return int(self.__y)

	def getMap(self):
		return self.__map

	def getUsername(self):
		return self.__username

	def getInventory(self):
		return self.__inventory

	def setSelectedTiles(self, tiles):

		if len(tiles) < 4:
			return False

		self.selectedTiles = tiles
		return True

	def battleTile(self, x, y):
		# When surfing only check water tiles.
		if self.moveType == "surf":
			if self.mapCollisions[y][x] != 2:
				return False
		else:
			if self.mapCollisions[y][x] != 3:
				return False

		return True

	def isPlayerInWater(self):
		return self.mapCollisions[self.__y][self.__x] == 2

	def isPlayerFacingWater(self):
		""" Check if the player is facing a water tile.

			Returns True if facing a water tile.
		"""
		try:
			if self.direction == "up":
				return self.mapCollisions[self.__y-1][self.__x] == 2
			elif self.direction == "down":
				return self.mapCollisions[self.__y+1][self.__x] == 2
			elif self.direction == "right":
				return self.mapCollisions[self.__y][self.__x+1] == 2
			elif self.direction == "left":
				return self.mapCollisions[self.__y][self.__x-1] == 2
			else:
				# Direction is set wrong so water can't be determined
				return False
		except:
			# Probably index out of bounds so definitely not water
			return False

	def moved(self, direction, bounded=False):
		""" Attempt to move the player in a specified direction.

			Returns boolean indicating whether the move was successful
		"""
		if direction == "up" and self.__isValidMove(self.__x, self.__y - 1, bounded):
			self.__y = self.__y - 1
			self.direction = "up"
			self.__updatePlayerMovements()
			return True
		elif direction == "down" and self.__isValidMove(self.__x, self.__y + 1, bounded):
			self.__y = self.__y + 1
			self.direction = "down"
			self.__updatePlayerMovements()
			return True
		elif direction == "right" and self.__isValidMove(self.__x + 1, self.__y, bounded):
			self.__x = self.__x + 1
			self.direction = "right"
			self.__updatePlayerMovements()
			return True
		elif direction == "left" and self.__isValidMove(self.__x - 1, self.__y, bounded):
			self.__x = self.__x - 1
			self.direction = "left"
			self.__updatePlayerMovements()
			return True

		# If we are here then we failed to move
		return False

	def directionOfTile(self, x, y):
		if x == self.__x and self.__y - 1 == y:
			return "up"
		elif x == self.__x and self.__y + 1 == y:
			return "down"
		elif x == self.__x + 1 and self.__y == y:
			return "right"
		elif x == self.__x - 1 and self.__y  == y:
			return "left"

		return None

	def __updatePlayerMovements(self):
		if self.mapMovements < 64:
			self.mapMovements += self.movementSpeed
		else:
			self.mapMovements = 0

		if self.moveType == "Bike":
			self.movementSpeed = 16 * self.movementSpeedMod

			if self.mount == "":
				self.mount = "Bike"
		else:
			self.movementSpeed = 8 * self.movementSpeedMod

		self.stepsWalked = self.stepsWalked + 1

		if self.stepsWalked >= 256:
			self.stepsWalked = 0
			self.stepsWalkedSignal.emit()


	def __isValidMove(self, y, x, bounded):
		""" Validate if player can move to given coordinate

			Check to see if the player can move to a given coordinate.
			Check if surfing/on land and if there is a selected are bound.
		"""

		valid = True
		coordKey = str(y) + "," + str(x)

		if bounded and self.selectedTiles == None:
			return False

		# When surfing only walk on water otherwise check land and grass.
		if self.moveType == "surf":
			if self.mapCollisions[x][y] != 2:
				valid = False
			if bounded and coordKey not in self.selectedTiles:
				valid = False
		else:
			if self.mapCollisions[x][y] != 0 and self.mapCollisions[x][y] != 3 and self.mapCollisions[x][y] != 6:
				valid = False
			if bounded and coordKey not in self.selectedTiles:
				valid = False

		return valid

	def getItemIndex(self, item):
		if item in self.__inventoryList:
			return self.__inventoryList.index(item)
		else:
			return -1

	def getBestFishingRod(self):
		rod = None

		if self.getItemIndex("Old Rod") != -1:
			rod = "Old Rod"

		if self.fishingLevel >= 5 and self.getItemIndex("Good Rod") != -1:
			rod = "Good Rod"

		if self.fishingLevel >= 20 and self.getItemIndex("Super Rod") != -1:
			rod = "Super Rod"

		if self.fishingLevel >= 50 and self.getItemIndex("Steel Rod") != -1:
			rod = "Steel Rod"

		return rod

	def getBestPotion(self):
		potion = None

		if self.getItemIndex("Hyper Potion") != -1:
			potion = "Hyper Potion"
		elif self.getItemIndex("Super Potion") != -1:
			potion = "Super Potion"
		elif self.getItemIndex("Potion") != -1:
			potion = "Potion"

		return potion

	def addItemToInventory(self, item, count):
		if item in self.__inventory:
			self.__inventory[item] = self.__inventory[item] + count
			if self.__inventory[item] <= 0:
				self.__inventory.pop(item)
				self.__inventoryList.remove(item)
		else:
			self.__inventory[item] = count
			self.__inventoryList.append(item)