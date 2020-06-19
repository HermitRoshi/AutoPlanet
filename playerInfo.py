import re
from pokemon import Pokemon
from utils.mapManager import MapManager
import xml.etree.ElementTree as ET

from PySide2.QtCore import QObject, Signal

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
		self.miningLevel = 0
		self.miningExp = 0
		self.team = []
		self.mount = ''
		self.direction = 'down'
		self.moveType = ''
		self.fishing = 0
		self.mining = False
		self.moving = False
		self.battle = False
		self.busy = False
		self.stepsWalked = 0
		self.mapMovements = 0
		self.movementSpeedMod = 0
		self.movementSpeed = 0
		self.activePokemon = 0
		self.currentRock = ''

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

		self.miningLevel = int(segments[segment_num + 47])
		self.miningExp = int(segments[segment_num + 48])

		self.activePokemon = self.getNextAlivePokemon()

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
			old_inventory = self.__inventory.copy()
			new_items = dict()
			self.__inventory = {}
			self.__inventoryList = []
			strings = data.replace('[','').replace("]]","").split('],')
			for item in strings:
				split_item = item.split(",")
				name = split_item[0]
				count = int(split_item[1])
				self.addItemToInventory(name, count)

				if name in old_inventory:
					if old_inventory[name] < count:
						new_items[name] = count - old_inventory[name]
				else:
					new_items[name] = count



	def updateInventoryXML(self, data):
		if data is not None:
			data = data.replace("<![CDATA[","").replace("]]","")
			root = ET.fromstring(data)

			items = root.findall('.//body/dataObj/obj/obj')
			temp_items_array = [None] * len(items)

			for item in items:
			    slot = int(item.attrib['o'])
			    item_vars = item.findall("var")
			    count = int(item_vars[0].text)
			    name = item_vars[1].text
			    
			    temp_items_array[slot] = [name, count]

			old_inventory = self.__inventory.copy()
			new_items = dict()

			if None not in temp_items_array and len(temp_items_array) > 0:
				self.__inventory = {}
				self.__inventoryList = []

				for item in temp_items_array:
					item_name = item[0]
					item_count = int(item[1])
					self.addItemToInventory(item_name, item_count)

					if item_name in old_inventory:
						if old_inventory[item_name] < item_count:
							new_items[item_name] = item_count - old_inventory[item_name]
					else:
						new_items[item_name] = item_count

			data_vars = root.findall('.//body/dataObj/var')
			temp_msg = None
			for avar in data_vars:
				if avar.attrib['n'] == "money":
					self.money = int(avar.text)
				if avar.attrib['n'] == "msg":
					temp_msg = avar.text

			return [temp_msg, new_items]

		return [None, new_items]

	def getBattleItems(self):
		''' Returns a list of all items usable in battle.

			Applies only to items in your inventory currently.
		'''
		usable_in_battle = ["Quick Ball", "Dive Ball", "Net Ball", "Nest Ball",
							"Repeat Ball", "Fast Ball", "Moon Ball", "Lure Ball", 
							"Level Ball", "Safari Ball", "Poke Ball (untradeable)", 
							"Great Ball (untradeable)", "Ultra Ball (untradeable)", 
							"Potion", "Super Potion", "Hyper Potion", "Poke Ball", 
							"Great Ball", "Ultra Ball", "Master Ball", "Halloween Ball", 
							"Halloween Candy", "Soda Pop", "Lemonade"]
		battle_items = []

		for item in self.__inventoryList:
			if item in usable_in_battle:
				battle_items.append(item)

		return battle_items

	def haveUsablePokemon(self):
		for pokemon in self.team:
			if pokemon.currentHealth > 0:
				return True

		return False
	def getNextAlivePokemon(self):
		for pokemon in range(len(self.team)):
			if self.team[pokemon].currentHealth > 0:
				return pokemon
		return -1

	def setActivePokemon(self):
		if self.getNextAlivePokemon() != -1:
			self.activePokemon = self.getNextAlivePokemon()
			return True
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

	def faceWater(self):
		''' Faces user towards water.

			If the user is already facing water nothing will change.
		'''
		if not self.isPlayerFacingWater():
			if self.mapCollisions[self.__y-1][self.__x] == 2:
				self.direction = "up"
			elif self.mapCollisions[self.__y+1][self.__x] == 2:
				self.direction = "down"
			elif self.mapCollisions[self.__y][self.__x+1] == 2:
				self.direction = "right"
			else:
				self.direction = "left"

		return self.isPlayerFacingWater()

	def isPlayerNearWater(self):
		''' Returns true if player is near water.

			Checks all four directions.
		'''

		if (self.mapCollisions[self.__y-1][self.__x] == 2 or
			self.mapCollisions[self.__y+1][self.__x] == 2 or
			self.mapCollisions[self.__y][self.__x+1] == 2 or
			self.mapCollisions[self.__y][self.__x-1] == 2):
			return True
		return False

	def isPlayerNearRock(self, rocks):
		""" Check if the player is facing a mining rock.

			Returns True if facing a mining rock.
		"""
		try:
			if ((str(self.__x) + "," + str(self.__y-1)) in rocks or
				(str(self.__x) + "," + str(self.__y+1)) in rocks or
				(str(self.__x+1) + "," + str(self.__y)) in rocks or
				(str(self.__x-1) + "," + str(self.__y)) in rocks):
				return True

			return False
		except:
			# Something went wrong, not near a rock for sure.
			return False

	def faceAvailableRock(self, rocks):
		up = str(self.__x) + "," + str(self.__y-1)
		down = str(self.__x) + "," + str(self.__y+1)
		right = str(self.__x+1)+ "," + str(self.__y)
		left = str(self.__x-1) + "," + str(self.__y)

		if up in rocks and rocks[up][3] == 1:
			self.direction = "up"
			self.currentRock = up
			return ["UP", self.__x, self.__y-1]

		elif down in rocks and rocks[down][3] == 1:
			self.direction = "down"
			self.currentRock = down
			return ["DOWN", self.__x, self.__y+1]

		elif right in rocks and rocks[right][3] == 1:
			self.direction = "right"
			self.currentRock = right
			return ["RIGHT", self.__x+1, self.__y]

		elif left in rocks and rocks[left][3] == 1:
			self.direction = "left"
			self.currentRock = left
			return ["LEFT", self.__x-1, self.__y]
		else:
			return ["NONE", 0, 0]

	def moved(self, direction, bounded=False):
		""" Attempt to move the player in a specified direction.

			Returns boolean indicating whether the move was successful
		"""
		if direction == "UP" and self.__isValidMove(self.__x, self.__y - 1, bounded):
			self.__y = self.__y - 1
			self.direction = "up"
			self.__updatePlayerMovements()
			return True
		elif direction == "DOWN" and self.__isValidMove(self.__x, self.__y + 1, bounded):
			self.__y = self.__y + 1
			self.direction = "down"
			self.__updatePlayerMovements()
			return True
		elif direction == "RIGHT" and self.__isValidMove(self.__x + 1, self.__y, bounded):
			self.__x = self.__x + 1
			self.direction = "right"
			self.__updatePlayerMovements()
			return True
		elif direction == "LEFT" and self.__isValidMove(self.__x - 1, self.__y, bounded):
			self.__x = self.__x - 1
			self.direction = "left"
			self.__updatePlayerMovements()
			return True

		# If we are here then we failed to move
		return False

	def directionOfTile(self, x, y):
		if x == self.__x and self.__y - 1 == y:
			return "UP"
		elif x == self.__x and self.__y + 1 == y:
			return "DOWN"
		elif x == self.__x + 1 and self.__y == y:
			return "RIGHT"
		elif x == self.__x - 1 and self.__y  == y:
			return "LEFT"

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

	def getWalkableDirections(self, bounded):
		""" Returns a list of walkable directions.

			Checks each of the four directions and if they're walkable
			adds them to the list. Returns the move list.
		"""
		moves = []
		if self.__isValidMove(self.__x, self.__y - 1, bounded):
			moves.append("UP")

		if self.__isValidMove(self.__x, self.__y + 1, bounded):
			moves.append("DOWN")

		if self.__isValidMove(self.__x + 1, self.__y, bounded):
			moves.append("RIGHT")

		if self.__isValidMove(self.__x - 1, self.__y, bounded):
			moves.append("LEFT")

		return moves

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

	def getItem(self, index):
		return self.__inventoryList[index]
		
	def getItemIndex(self, item):
		if item in self.__inventoryList:
			return self.__inventoryList.index(item)
		else:
			return -1

	def getCatchingPokeball(self, rule_ball):
		if rule_ball == "Any":
			usable_balls = ["Quick Ball", "Dive Ball", "Net Ball", "Nest Ball",
							"Repeat Ball", "Fast Ball", "Moon Ball", "Lure Ball", 
							"Level Ball", "Safari Ball", "Poke Ball (untradeable)", 
							"Great Ball (untradeable)", "Ultra Ball (untradeable)", 
							"Poke Ball", "Great Ball", "Ultra Ball", "Halloween Ball"]
			for item in self.__inventoryList:
				if item in usable_balls:
					return self.__inventoryList.index(item)

			return -1
		else:
			ball_index =  self.getItemIndex(rule_ball)
			if ball_index == -1:
				return self.getItemIndex(rule_ball + " (untradeable)")

			return ball_index

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

	def getBestPickaxe(self):
		pickaxe = None

		if self.getItemIndex("Old Pickaxe") != -1:
			pickaxe = "Old Pickaxe"

		if self.miningLevel >= 5 and self.getItemIndex("Good Pickaxe") != -1:
			pickaxe = "Good Pickaxe"

		if self.miningLevel >= 20 and self.getItemIndex("Super Pickaxe") != -1:
			pickaxe = "Super Pickaxe"

		if self.miningLevel >= 50 and self.getItemIndex("Steel Pickaxe") != -1:
			pickaxe = "Steel Pickaxe"

		if self.miningLevel >= 100 and self.getItemIndex("Master Pickaxe") != -1:
			pickaxe = "Master Pickaxe"

		return pickaxe

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
		elif count > 0:
			self.__inventory[item] = count
			self.__inventoryList.append(item)