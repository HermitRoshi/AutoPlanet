import time
import math
import random
import ast

from functools import partial
from threading import Thread, Timer
from webSession import WebSession
from threadedSocket import ThreadedSocket
from playerInfo import PlayerInfo
from pokemon import WildPokemon
from utils.constants import CONSTANTS
from utils.repeatTimer import RepeatTimer
from message import Message, MessageTypeEnum
from botRules import BotRules
from utils.pathfinding import *
from utils.utils import getTimeMillis, getRandomString, stringToMd5
from utils.notificationHandler import NotificationHandler

from PySide2.QtCore import QObject, Signal
from PySide2.QtWidgets import QWidget, QMessageBox

class GameHandler(QObject):
	infoSignal = Signal(int, int)
	teamSignal = Signal(object)
	inventorySignal = Signal(object)
	positionSignal = Signal(str, int, int, str, bool)
	logSignal = Signal(str)
	chatSignal = Signal(str, str, str, str)
	connectedSignal = Signal(bool)
	runningSignal = Signal(bool)
	mountChanged = Signal(str)
	historySignal = Signal(int, int, object, object)
	rockSignal = Signal(object)
	globalMarketplace = Signal(object)
	playersSignal = Signal(object)

	def __init__(self, gameVersion, key1, key2, sessionCookie, userAgent, proxy):
		super(GameHandler, self).__init__()
		self.__gameVersion = gameVersion
		self.__key1 = key1
		self.__key2 = key2
		self.__sessionCookie = sessionCookie
		self.__userAgent = userAgent
		self.__proxy = proxy
		self.__startTimeMillis = getTimeMillis()

		# Handles web login and session
		self.__webSession = WebSession(self.__sessionCookie, self.__userAgent, self.__proxy)

		# Socket used for game connection
		self.__gameSocket = ThreadedSocket(CONSTANTS.GAME_IP, 
										   CONSTANTS.GAME_PORT,
										   self.__proxy)
		self.__gameSocket.receiveSignal.connect(self.__processInboundData)
		self.__gameSocket.timeoutSignal.connect(self.__catchTimeout)

		# Bot state
		self.__running = False

		# Game connection state
		self.__connected = False

		# Did session time out
		self.__timedOut = False

		# Are we taking a break
		self.__breakTime = False
		self.__whenToBreakMs = 2700000
		self.__loginTimer = None

		# Thread to send the game heartbeat
		self.__heartbeat_thread = Thread(target=self.__sendHeartbeat, name="Heartbeat Thread")
		self.__heartbeat_thread.setDaemon(True)

		# Thread for the main bot loop
		self.__main_bot_thread = None

		# Thread for user issued walk commands
		self.__walk_thread = None

		# Set of rules the bot has to follow includes catch list and such
		self.__botRules = BotRules()

		# Dictionary of players that have private messaged the player
		self.__pmNames = dict()

		# Player information 
		self.__playerInfo = PlayerInfo()
		self.__playerInfo.stepsWalkedSignal.connect(self.__sendB38)

		# Information about current wild battle
		self.wildPokemon = None
		self.myTurn = False
		self.battleWon = False
		self.hook = False

		# Last X and Y reported to the server
		self.__lastX = 0
		self.__lastY = 0
		self.__updateXYTimerStart = RepeatTimer(CONSTANTS.GAME_UPDATEXY_RATE_SEC, self.__updateXY)
		self.__updateXYTimerMap = RepeatTimer(CONSTANTS.GAME_UPDATEXY_RATE_SEC, self.__updateXY)
		self.__saveDataTimer = RepeatTimer(CONSTANTS.GAME_SAVEDATA_RATE_SEC, self.__sendB26)
		self.__fishingTimer = RepeatTimer(2.1, self.__sendB70)
		self.__miningTimer = RepeatTimer(2.5, self.__sendB163)

		# Session information
		self.__battles = 0
		self.__moneyEarned = 0
		self.__pokemonEncountered = dict()
		self.__itemsObtained = dict()
		self.__username = None
		self.__password = None
		self.__selectedTiles = None
		self.__timeoutX = 0
		self.__timeoutY = 0
		self.__backToPosTimer = None
		self.__sendRulesTimer = None
		self.__rocks = dict()
		self.__players = dict()
		self.__requests = dict()
		self.__notificationHandler = NotificationHandler()

		# Bot detection
		self.botWatch = False
		self.botWatchToken = ''

	def toggleLogin(self, username, password):
		""" Toggles login.
			
			If connected the user is disconnected.
			Otherwise, attempts to log into the website and the game.
		"""

		# Save off username and password used to login for reconnect
		self.__username = username
		self.__password = password

		# If connected then disconnect
		if self.__connected:
			self.disconnect()
		else:
			# Reset connection timer
			self.__startTimeMillis = getTimeMillis()
			self.__whenToBreakMs = random.randint(10800000, 14000000)

			if self.__loginTimer != None and self.__loginTimer.is_alive():
				self.__loginTimer.cancel()

			if self.__proxy[0] == "Enabled":
				self.__logData("<font color='yellow'>Attempting connection with proxy <b>enabled</b></font>")
			else:
				self.__logData("<font color='yellow'>Attempting connection with proxy <b>disabled</b></font>")

			self.__logData("Creating web session...")
			if self.__webSession.login(username, password):
				self.__logData("Web session created.")
				self.__logData("Connecting to the game server...")
				self.__gameSocket.connectSocket()
				self.__gameSocket.sendData(CONSTANTS.GAME_POLICY_MSG)
				self.__playerInfo.setUsername(self.__webSession.getUsername())
			else:
				self.__logData("Failed to create web session.")

	def disconnect(self):
		""" Disconnect from game server.

			Disconnect from web session and game connection.
			Reset game variables to initial state.
		"""

		# Recreate the web session
		self.__webSession = WebSession(self.__sessionCookie, self.__userAgent, self.__proxy)

		# Close the game socket
		self.__gameSocket.close()

		# Reset bot state
		self.stopBotting()

		# Reset game connection state
		self.__connected = False

		# Socket used for game connection
		self.__gameSocket = ThreadedSocket(CONSTANTS.GAME_IP, 
										   CONSTANTS.GAME_PORT,
										   self.__proxy)
		self.__gameSocket.receiveSignal.connect(self.__processInboundData)
		self.__gameSocket.timeoutSignal.connect(self.__catchTimeout)

		self.__heartbeat_thread = Thread(target=self.__sendHeartbeat, name="Heartbeat Thread")
		self.__heartbeat_thread.setDaemon(True)

		# Clear player info
		self.__playerInfo = PlayerInfo()
		self.__playerInfo.stepsWalkedSignal.connect(self.__sendB38)

		# Reset fishing hook and stop timer
		self.hook = False
		if self.__fishingTimer.is_running:
			self.__fishingTimer.stop()

		# Last X and Y reported to the server
		self.__lastX = 0
		self.__lastY = 0
		self.__updateXYTimerStart.stop()
		self.__updateXYTimerMap.stop()
		self.__saveDataTimer.stop()

		# Update the display with signals
		self.connectedSignal.emit(False)
		self.teamSignal.emit(self.__playerInfo.team)
		self.inventorySignal.emit(self.__playerInfo.getInventory())
		keep_data = self.__breakTime or self.__timedOut
		self.positionSignal.emit(self.__playerInfo.cleanMapName, self.__playerInfo.getX(), self.__playerInfo.getY(), self.__playerInfo.direction, keep_data)
		self.__logData("You have been logged out.")

		# If we disconnected because of a timeout... reconnect
		if self.__timedOut:
			self.__logData("Attempting to reconnect...")
			self.toggleLogin(self.__username, self.__password)
		elif self.__breakTime:
			break_length_seconds = random.randint(180, 500)
			time.sleep(break_length_seconds)
			self.toggleLogin(self.__username, self.__password)
		else:
			# Session information
			self.__battles = 0
			self.__moneyEarned = 0
			self.__pokemonEncountered = dict()
			self.__itemsObtained = dict()
			self.historySignal.emit(self.__battles, self.__moneyEarned, self.__pokemonEncountered, self.__itemsObtained)
		self.__players = dict()
		self.playersSignal.emit(self.__players)

	def __catchTimeout(self):
		self.__logData("Connection timed out...")
		if self.__running or self.__timedOut:

			# Need to cancel these timers if they're running already
			if self.__backToPosTimer is not None and self.__backToPosTimer.is_alive():
				self.__backToPosTimer.cancel()

			if self.__sendRulesTimer is not None and self.__sendRulesTimer.is_alive():
				self.__sendRulesTimer.cancel()

			if not self.__timedOut:
				self.__timeoutX = self.__playerInfo.getX()
				self.__timeoutY = self.__playerInfo.getY()
			self.__timedOut = True
			self.disconnect()

	def __initiateBreak(self):
		self.__logData("Logging out for a break...")
		if self.__running:

			# Need to cancel these timers if they're running already
			if self.__backToPosTimer is not None and self.__backToPosTimer.is_alive():
				self.__backToPosTimer.cancel()

			if self.__sendRulesTimer is not None and self.__sendRulesTimer.is_alive():
				self.__sendRulesTimer.cancel()

			self.__timeoutX = self.__playerInfo.getX()
			self.__timeoutY = self.__playerInfo.getY()

			self.__breakTime = True
			self.disconnect()

	def __restartBot(self):
		""" Restarts the bot.

			Assume we have connection at this point.
			Finish any battles from last session.
			Move player to previous spot if they respawned elsewhere.
			Begin botting.
		"""
		# Notify user
		self.__logData("Resuming bot...")

		# Compute path to previous location
		path = astar(self.__playerInfo.mapCollisions,  
					(self.__playerInfo.getY(),self.__playerInfo.getX()), 
					(self.__timeoutY, self.__timeoutX), self.__playerInfo.isPlayerInWater())
		# Remove start position as the player is there already
		if path is not None:
			path.pop(0)

		# Walk back timer
		self.__backToPosTimer = Timer(5, self.walkCommand, args=(path,))
		self.__backToPosTimer.setDaemon(True)
		self.__backToPosTimer.start()

		# Restart botting timer
		self.__sendRulesTimer = Timer(50, self.setRules, [self.__selectedTiles, self.__botRules])
		self.__sendRulesTimer.setDaemon(True)
		self.__sendRulesTimer.start()
		
	def __handleLogin(self, message):
		if message.getMessageType() == MessageTypeEnum.POLICY:
			if self.__gameSocket.getShutdownCount() < 1:
				self.__gameSocket.shutdown()
				self.__gameSocket.connectSocket()
				response_timer = Timer(0.2, self.__sendVersion)
				response_timer.setDaemon(True)
				response_timer.start()

		elif message.getMessageType() == MessageTypeEnum.MSG:
			if message.getMessageAction() == 'apiOK':
				self.__logData("Authenticating...")
				time.sleep(0.2)
				self.__gameSocket.sendData(self.__webSession.getLoginString())
			elif message.getMessageAction() == 'rmList':
				time.sleep(0.2)
				self.__gameSocket.sendData(CONSTANTS.GAME_AUTOJOIN_MSG)
			elif message.getMessageAction() == 'joinOK':
				self.__logData("Loading Game Data...")
				response_timer = Timer(0.2, self.__sendB61)
				response_timer.setDaemon(True)
				response_timer.start()

		elif message.getMessageType() == MessageTypeEnum.XT:
			if message.getMessageAction() == 'l' and message.getMessageCode() == '-1':
				time.sleep(0.2)
				self.__gameSocket.sendData(CONSTANTS.GAME_RMLIST_MSG)
			elif message.getMessageAction() == 'r10':
				self.__playerInfo.parseData(message.getMessageRaw())
				self.__lastX = self.__playerInfo.getX()
				self.__lastY = self.__playerInfo.getY()
				self.__updateXYTimerStart.start()
				self.__updateXYTimerMap.start()
				self.__saveDataTimer.start()
				response_timer = Timer(0.9, self.__sendB74)
				response_timer.setDaemon(True)
				response_timer.start()
			elif message.getMessageAction() == 'b88' and message.getMessageCode() == '-1':
				if self.__playerInfo.mapCollisions != None:
					if self.__playerInfo.isPlayerInWater():
						self.__changeMount("surf")
					response_timer = Timer(0.2, self.__sendB5)
					response_timer.setDaemon(True)
					response_timer.start()
				else:
					self.__logData("<font color='red'>ERROR: No map file for: <b>{}</b></font>".format(self.__playerInfo.cleanMapName))
					self.disconnect()
			elif message.getMessageAction() == 'b5' and message.getMessageCode() == '-1':
				self.__sendB55()
				self.__connected = True
				self.__heartbeat_thread.start()
				self.__logData("Connected")
				self.teamSignal.emit(self.__playerInfo.team)
				self.inventorySignal.emit(self.__playerInfo.getInventory())
				keep_data = self.__timedOut or self.__breakTime
				self.positionSignal.emit(self.__playerInfo.cleanMapName, self.__playerInfo.getX(), self.__playerInfo.getY(), self.__playerInfo.direction, keep_data)
				self.connectedSignal.emit(True)
				self.infoSignal.emit(self.__playerInfo.money, self.__playerInfo.credits)
				self.__handleMapUpdate(message.getMessageRaw())
				if (self.__playerInfo.getItemIndex("Bike") != -1 and
					self.__playerInfo.moveType != "surf" and not self.__playerInfo.battle):
					self.__changeMount("Bike")
				if self.__timedOut or self.__breakTime:
					self.__restartBot()
					self.__timedOut = False
					self.__breakTime = False
			elif message.getMessageAction() == "w2":
				self.__handleNewBattle(message.getMessageRaw())

	def updateProxy(self, proxy):
		self.__proxy = proxy

	def setLocation(self, mapname, x, y):
		if self.__connected:
			if self.__running:
				self.__logData("<font color='red'>ERROR: Must stop botting to load location!</font>")
			elif self.__playerInfo.moving:
				self.__logData("<font color='red'>ERROR: Must stop moving to load location!</font>")
			else:
				location = [mapname, x, y]
				if self.__playerInfo.exitMap(location):
					self.positionSignal.emit(location[0], location[1], location[2], self.__playerInfo.direction, False)
					self.__handleMapChange()
					self.__logData("<font color='green'>Succesfully loaded location!</font>")
				else:
					self.__logData("<font color='red'>ERROR: Failed to load location!</font>")
		else:
			self.__logData("<font color='red'>ERROR: Must be connected to game server to load location!</font>")

	def __logData(self, message):
		if message is not None and len(message) > 1:
			self.logSignal.emit(message)

	def __processInboundData(self, data):
		if data is not None:
			message = Message(data)
			if self.__connected:
				self.__proccesMessage(message)
			else:
				self.__handleLogin(message)

	def __proccesMessage(self, message):
		if message.getMessageAction() == "pmsg":
			self.__processPmsg(message.getMessageRaw())
		elif message.getMessageAction() == "a":
			self.__handleAddPlayer(message.getMessageRaw().split('`'), True)
		elif message.getMessageAction() == "b":
			self.__handleAddPlayer(message.getMessageRaw().split('`'), False)
		elif message.getMessageAction() == "w":
			# Wild battle
			self.__handleNewBattle(message.getMessageRaw())
		elif message.getMessageAction() == "w2":
			# Wild battle from previous login
			self.__handleNewBattle(message.getMessageRaw())
		elif message.getMessageAction() == "c":
			self.__handleBattleMoveMessage(message.getMessageRaw().split('`'))
		elif message.getMessageAction() == "r17":
			# This part is a little hacky but its needed to prevent
			# the bot from stopping during a request attack
			if "Please finish what you are doing first." in message.getMessageRaw().split('`')[4]:
				if self.__playerInfo.battle and self.__playerInfo.busy:
					self.__playerInfo.battle = False
			self.logSignal.emit("<font color='orange'>" + message.getMessageRaw().split('`')[4].replace("FFFFFF", "6a0dad") + "</font>")
		elif message.getMessageAction() == "xtRes":
			if message.getXmlCmd() == "askEvolve":
				if self.__botRules.evolve:
					self.__logData("Accepting Evolve.")
					self.__sendB18()
				else:
					self.__logData("Denying Evolve")
					self.__sendB19()
			elif message.getXmlCmd() == "learnMove":
				self.__logData("Being prompted to learn new move.")
				self.__handleLearnMove(int(message.getValue("slot")))
			elif message.getXmlCmd() == "clanRequest":
				self.__playerInfo.busy = True
				self.__logData("<font color='red'>Denying a clan request!</font>")
				response_timer = Timer(random.randint(2,7), self.__handleClanInvite)
				response_timer.setDaemon(True)
				response_timer.start()
				clan_settings = self.__botRules.clanNotifications()
				self.__notificationHandler.handleNotification("clan", clan_settings[0] , clan_settings[1])
			elif message.getXmlCmd() == "updateInventory":
				inv_data = self.__playerInfo.updateInventoryXML(message.getMessageRaw())
				self.inventorySignal.emit(self.__playerInfo.getInventory())
				# Update new items obtained if there are any
				if len(inv_data[1]) > 0:
					for item in inv_data[1]:
						if item in self.__itemsObtained:
							self.__itemsObtained[item] += inv_data[1][item]
						else:
							self.__itemsObtained[item] = inv_data[1][item]
					self.historySignal.emit(self.__battles, self.__moneyEarned, self.__pokemonEncountered, self.__itemsObtained)
			elif message.getXmlCmd() == "buyItem":
				inv_data = self.__playerInfo.updateInventoryXML(message.getMessageRaw())
				if inv_data[0] != None:
					self.__logData("<font color='green'>{}.</font>".format(inv_data[0]))
				self.inventorySignal.emit(self.__playerInfo.getInventory())
				self.infoSignal.emit(self.__playerInfo.money, self.__playerInfo.credits)
			elif message.getXmlCmd() == "b2adb2":
				self.botWatch = True
				self.botWatchToken = str(message.getValue("a"))
				self.__botRules.speed = 2
			elif message.getXmlCmd() == "b2adb2z":
				self.botWatch = False
				self.__botRules.speed = 3
		elif message.getMessageAction() == "ui":
			# Updating inventory and team
			split_string = message.getMessageRaw().split('`')
			self.__playerInfo.updateInventory(split_string[4])
			self.__playerInfo.updateTeam(split_string[5])
			self.teamSignal.emit(self.__playerInfo.team)
			self.inventorySignal.emit(self.__playerInfo.getInventory())
		elif message.getMessageAction() == "r4" or message.getMessageAction() == "r5":
			# MarketpalceSearchMessage
			self.__handleHeldItem(message.getMessageAction(), message.getMessageRaw())
		elif message.getMessageAction() == "r27":
			# MarketpalceSearchMessage
			self.__handleMarketplaceSearchResponse(message.getMessageRaw())
		elif message.getMessageAction() == "r28":
			# Marketplace buy message
			self.__handleMarketplaceBuyResponse(message.getMessageRaw())
		elif message.getMessageAction() == "r36":
			# Private message
			self.__processR36(message.getMessageRaw())
		elif message.getMessageAction() == "r59":
			self.__handleClanMessage(message.getMessageRaw())
		elif message.getMessageAction() == "r62":
			split_string = message.getMessageRaw().split('`')
			self.__handleRemovePlayer(split_string[4])
		elif message.getMessageAction() == "b5":
			# Map update
			self.__handleMapUpdate(message.getMessageRaw())
		elif message.getMessageAction() == "b121":
			# This mean we are prompted to hook a pokemon
			self.__fishingTimer.stop()
			self.hook = True
		elif message.getMessageAction() == "b86":
			# Add an item to inventory
			split_string = message.getMessageRaw().split('`')
			split_string = split_string[4].split(",")
			self.__playerInfo.addItemToInventory(split_string[0], int(split_string[1]))
			if int(split_string[1]) > 0:
				if split_string[0] in self.__itemsObtained:
					self.__itemsObtained[split_string[0]] += int(split_string[1])
				else:
					self.__itemsObtained[split_string[0]] = int(split_string[1])
			self.historySignal.emit(self.__battles, self.__moneyEarned, self.__pokemonEncountered, self.__itemsObtained)
			self.inventorySignal.emit(self.__playerInfo.getInventory())
		elif message.getMessageAction() == "b87":
			# Remove an item from inventory
			split_string = message.getMessageRaw().split('`')
			split_string = split_string[4].split(",")
			self.__playerInfo.addItemToInventory(split_string[0], -int(split_string[1]))
			self.inventorySignal.emit(self.__playerInfo.getInventory())
		elif message.getMessageAction() == "b95":
			for pokemon in self.__playerInfo.team:
				pokemon.currentHealth = pokemon.health
			self.teamSignal.emit(self.__playerInfo.team)
		elif message.getMessageAction() == "b164":
			self.__handleMiningRockDepleted(message.getMessageRaw())
		elif message.getMessageAction() == "b165":
			self.__handleMiningRockRestored(message.getMessageRaw())
		elif message.getMessageAction() == "b179":
			# This is a battle request
			self.__playerInfo.busy = True
			self.__logData("<font color='red'>Denying a battle request!</font>")
			response_timer = Timer(random.randint(3,9), self.__handleBattleInvite)
			response_timer.setDaemon(True)
			response_timer.start()
			battle_settings = self.__botRules.battleNotifications()
			self.__notificationHandler.handleNotification("battle", battle_settings[0] , battle_settings[1])
		elif message.getMessageAction() == "b185":
			# This is a trade request
			self.__playerInfo.busy = True
			self.__logData("<font color='red'>Denying a trade request!</font>")
			response_timer = Timer(random.randint(2,10), self.__sendB17)
			response_timer.setDaemon(True)
			response_timer.start()
			trade_settings = self.__botRules.tradeNotifications()
			self.__notificationHandler.handleNotification("trade", trade_settings[0] , trade_settings[1])
		elif message.getMessageAction() == "userGone":
			user_id = message.getUserId()
			if user_id in self.__players:
				del self.__players[user_id]
				self.playersSignal.emit(self.__players)

	def __handleAddPlayer(self, data, addBack=False):
		if self.__playerInfo.characterCreated != 0 and addBack:
			self.__sendB56(data)

		player_name = data[4]
		player_id = data[8]
		player_type = data[21]

		if player_id not in self.__players:
			self.__players[player_id] = [player_name, player_type]
			self.playersSignal.emit(self.__players)

		if player_name.lower() == "brody" or player_name.lower() == "anubisius":
			print("{} is on your map!!".format(player_name))

	def __handleRemovePlayer(self, player_to_remove):
		temp_players = self.__players.copy()

		for player in temp_players:
			if temp_players[player][0] == player_to_remove:
				if player in self.__players:
					del self.__players[player]
					self.playersSignal.emit(self.__players)
					return

	def __handleNewBattle(self, data):
		self.wildPokemon = WildPokemon(data)

		self.myTurn = True
		self.__playerInfo.battle = True
		self.__battles = self.__battles + 1

		next_active = self.__playerInfo.getNextAlivePokemon()
		if next_active != -1:
			self.__playerInfo.activePokemon = next_active
		else:
			# This is unlikely to happen but as a safety net we'll disconnect
			self.disconnect()

		name = self.wildPokemon.name
		if(self.wildPokemon.shiny):
			name = "[S]" + name
		elif(self.wildPokemon.elite):
			name = "[E]" + name

		if name in self.__pokemonEncountered.keys():
			self.__pokemonEncountered[name] += 1
		else:
			self.__pokemonEncountered[name] = 1

		self.historySignal.emit(self.__battles, self.__moneyEarned, self.__pokemonEncountered, self.__itemsObtained)
		self.__logData("<font color='#06B3F8'><b>Battle! Pokemon:[{}][{}]</b></font>".format(name, self.wildPokemon.level))

	def __handleHeldItem(self, what, message):
		split_string = message.split("`")
		if what == "r4":
			pokemon = int(split_string[4])
			item_index = int(split_string[5])
			item = self.__playerInfo.getItem(item_index)

			self.__playerInfo.team[pokemon].item = item
			self.__playerInfo.addItemToInventory(item, -1)
			self.__logData("<font color='#00FF08'>Gave {} to {}!</font>".format(item, self.__playerInfo.team[pokemon].name))
		elif what == "r5":
			pokemon = int(split_string[4])
			item = self.__playerInfo.team[pokemon].item
			self.__playerInfo.addItemToInventory(item, 1)
			self.__playerInfo.team[pokemon].item = "none"
			self.__logData("<font color='#00FF08'>Removed {} from {}!</font>".format(item, self.__playerInfo.team[pokemon].name))

		self.inventorySignal.emit(self.__playerInfo.getInventory())
		self.teamSignal.emit(self.__playerInfo.team)

	def removeItem(self, pokemon):
		if self.__connected:
			if self.__running:
				self.__logData("<font color='red'>ERROR: Must stop botting to remove item!</font>")
			elif self.__playerInfo.moving:
				self.__logData("<font color='red'>ERROR: Must stop moving to remove item!</font>")
			else:
				if self.__playerInfo.team[pokemon].item != "none":
					self.__sendXtMessage("b59", [pokemon])
				else:
					self.__logData("<font color='red'>ERROR: That pokemon has no item!</font>")
		else:
			self.__logData("<font color='red'>ERROR: Must be connected to remove item!</font>")

	def giveItem(self, item, pokemon):
		if self.__connected:
			if self.__running:
				self.__logData("<font color='red'>ERROR: Must stop botting to give item!</font>")
			elif self.__playerInfo.moving:
				self.__logData("<font color='red'>ERROR: Must stop moving to give item!</font>")
			else:
				index = self.__playerInfo.getItemIndex(item)
				if index != -1:
					if self.__playerInfo.team[pokemon].item == "none":
						self.__sendXtMessage("b58", [pokemon, index])
					else:
						self.__logData("<font color='red'>ERROR: That pokemon is already holding an item!</font>")
				else:
					self.__logData("<font color='red'>ERROR: Cannot find item in inventory!</font>")
		else:
			self.__logData("<font color='red'>ERROR: Must be connected to give item!</font>")

	def handleVendorBuy(self, item, count):
		if self.__connected and not self.__running and not self.__playerInfo.battle:
			play_time = str(getTimeMillis() - self.__startTimeMillis)
			packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
			packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

			msg_b8 = ("<msg t='xt'><body action='xtReq' r='1'>" +
					  "<![CDATA[<dataObj><var n='name' t='s'>PokemonPlanetExt</var>" +
					  "<var n='cmd' t='s'>b8</var><obj t='o' o='param'>" +
					  "<var n='amount' t='n'>" + str(count) + "</var>" +
					  "<var n='buyNum' t='n'>"+ str(item) + "</var>" +
					  "<var n='pke' t='s'>" + packet_key_crypto + "</var>" +
					  "<var n='pk' t='s'>" + packet_key + "</var>" +
					  "<var n='te' t='n'>" + play_time + "</var>" +
					  "</obj></dataObj>]]></body></msg>\x00")

			self.__gameSocket.sendData(msg_b8)
		else:
			self.__logData("<font color='red'>ERROR: To use vendor you must be logged in and not running/battle.</font>")


	def searchMarketplace(self, name, type="all"):
		if self.__connected and not self.__running and not self.__playerInfo.battle:
			self.__sendXtMessage("r27", [type, name])
		else:
			self.__logData("<font color='red'>ERROR: To use marketplace you must be logged in and not running/battle.</font>")

	def buyMarketplace(self, id):
		self.__sendXtMessage("r28", [id])

	def __handleMarketplaceBuyResponse(self, message):
		split_string = message.split("`")
		object_type = str(split_string[4])
		item = split_string[5]
		count = int(split_string[6])
		
		if object_type == "item":
			money = int(split_string[7])
			self.__playerInfo.addItemToInventory(item, count)
			self.__playerInfo.money = money

			# Retrieve item from item box
			self.__sendXtMessage("b83", [])

			self.infoSignal.emit(self.__playerInfo.money, self.__playerInfo.credits)
			self.inventorySignal.emit(self.__playerInfo.getInventory())
		elif object_type == "pokemon":
			count = 1
			item = item.replace("]", "").replace("[", "").split(",")[33]

		self.__logData("<font color='#00FF08'>Bought {} x{}!</font>".format(item, count))

	def __handleMarketplaceSearchResponse(self, message):
		results = message.split("`")[4:]
		self.globalMarketplace.emit(results)

	def __handleBattleInvite(self):
		''' Handles battle invite.

			By hande I mean it denies it.
		'''
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

		msg_b14 = ("<msg t='xt'> <body action='xtReq' r='1'> <![CDATA[<dataObj>" +
				   "<var n='name' t='s'>PokemonPlanetExt</var>" +
				   "<var n='cmd' t='s'>b14</var>" +
				   "<obj t='o' o='param'>" +
						"<var n='pke' t='s'>" + packet_key_crypto + "</var>" +
						"<var n='pk' t='s'>" + packet_key + "</var>" +
						"<var n='te' t='n'>" + play_time + "</var>" +
				   "</obj></dataObj>]]></body></msg>\x00")

		if self.botWatch:
			self.__generateFakeMouseClick(9)

		self.__gameSocket.sendData(msg_b14)

		self.__playerInfo.busy = False

	def __handleClanInvite(self):
		''' Handles clan invite.

			By hande I mean it denies it.
		'''

		# Not sure if this key changes often. It might...
		cmd = stringToMd5("declineClanInvitekzf76adngjfdgh12m7mdlbfi9proa15gjqp0sd3mo1lk7w90cd" + self.__webSession.getUsername())

		msg_b17 = ("<msg t='xt'> <body action='xtReq' r='1'> <![CDATA[<dataObj>" +
				   "<var n='name' t='s'>PokemonPlanetExt</var>" +
				   "<var n='cmd' t='s'>" + cmd +"</var>" +
				   "<obj t='o' o='param'>" +
						"<var n='pke' t='s'>" + packet_key_crypto + "</var>" +
						"<var n='pk' t='s'>" + packet_key + "</var>"
						"<var n='te' t='n'>" + play_time + "</var>"
				   "</obj></dataObj>]]></body></msg>\x00")

		if self.botWatch:
			self.__generateFakeMouseClick(9)

		self.__gameSocket.sendData(msg_b17)

		self.__playerInfo.busy = False

	def __sendFakeKeyLog(self, key):
		''' Sends the server a fake key.

			The server sometimes askes for key press log.
			This is to detect bots and ensure the user is actually
			pressing the keys and also not using a macro to press same key
			over and over again. This function sends a key message.
		'''
		if self.botWatch:
			click_time = str(getTimeMillis() - self.__startTimeMillis)
			self.__sendXtMessage("b69", [key, click_time, self.botWatchToken], header=False)

	def __sendFakeMouseClick(self, x, y):
		''' Sends the server a fake mouse click.

			The server sometimes askes for mouse click log.
			This is to detect bots and ensure the user is actually
			clicking the mouse and also not using a macro to press same key
			over and over again. This function sends a mouse click message.
		'''
		if self.botWatch:
			click_time = str(getTimeMillis() - self.__startTimeMillis)
			self.__sendXtMessage("b68", [x, y, click_time, self.botWatchToken], header=False)


	def __generateFakeMouseClick(self, button):
		''' Generate x,y coordinates to represent a mouse click

			Coordinates are generated based on which button is clicked.
		'''
		x = 0
		y = 0

		if button == 1:
			x = random.randint(205, 320)
			y = random.randint(420, 466)
		elif button == 2:
			x = random.randint(205, 320)
			y = random.randint(475, 513)
		elif button == 3:
			x = random.randint(350, 455)
			y = random.randint(420, 466)
		elif button == 4:
			x = random.randint(350, 455)
			y = random.randint(475, 513)
		elif button == 5:
			x = random.randint(480, 595)
			y = random.randint(420, 466)
		elif button == 6: 
			x = random.randint(480, 595)
			y = random.randint(475, 513)
		elif button == 7: 
			x = random.randint(332, 360)
			y = random.randint(425, 513)
		elif button == 8: 
			x = random.randint(370, 460)
			y = random.randint(425, 513)
		elif button == 9: 
			x = random.randint(550, 618)
			y = random.randint(335, 365)
		elif button >= 10 and button < 100:
			item_width = 118
			item_height = 50
			item_gap = 52
			min_x = 55
			min_y = 7

			pokemon_slot = button - 10

			x = pokemon_slot * (item_width + item_gap) + min_x

			x = random.randint(x, x + item_width)
			y = random.randint(min_y, item_height)
		elif button >= 100:
			item_size = 32
			item_gap = 5
			min_x = 23
			min_y = 237

			used_item = button - 100
			item_column = used_item % 5
			item_row = math.floor(used_item / 5)

			x = item_column * (item_size + item_gap) + min_x
			y = item_row * (item_size + item_gap) + min_y

			x = random.randint(x, x + item_size)
			y = random.randint(y, y + item_size)

		self.__sendFakeMouseClick(x, y)

		# Double click for inventory items
		if button >= 100:
			time.sleep(random.uniform(0.07, 0.15))
			self.__sendFakeMouseClick(x, y)

	def __handleLearnMove(self, slot):
		if len(self.__playerInfo.team[slot].moves) == 1:
			self.__sendB0(1)
		elif len(self.__playerInfo.team[slot].moves) == 2:
			self.__sendB0(2)
		elif len(self.__playerInfo.team[slot].moves) == 3:
			self.__sendB0(3)
		else:
			self.__sendB0(self.__botRules.learnMove)

	def __handleBattleMoveMessage(self, data):
		self.__playerInfo.updateTeam(data[12])
		messages = data[11].split("|")
		for message in messages:
			message = message.split(",")
			log_message = message[0]
			if message[1] != "":
				log_message = log_message + " Dealing " +  message[1] + " damage."
			self.__logData("<font color='#3d84a8'>" + log_message + "</font>")
		self.wildPokemon.updateFromCMessage(data[13])
		self.teamSignal.emit(self.__playerInfo.team)

		# The battle has been won
		if data[4] == "W":
			# Check if we were awarded money and update it
			if data[10] != "0":
				self.__logData("<font color='#1fab89'>Earned <b>$" + str(int(data[10]) - int(self.__playerInfo.money)) + "</b> from battle.</font>")
				self.__moneyEarned = self.__moneyEarned + int(data[10]) - int(self.__playerInfo.money)
				self.__playerInfo.money = int(data[10])

			# Update player info display
			self.infoSignal.emit(self.__playerInfo.money, self.__playerInfo.credits)

			# Battle is over with a victory
			self.battleWon = True
			self.myTurn = False
			self.__playerInfo.battle = False
			self.wildPokemon = None
			next_active = self.__playerInfo.getNextAlivePokemon()
			if next_active != -1:
				self.__playerInfo.activePokemon = next_active
			else:
				# This is unlikely to happen but as a safety net we'll disconnect
				self.disconnect()
			if self.__botRules is not None and self.__botRules.takeLogoutBreak():
				if (getTimeMillis() - self.__startTimeMillis) >= self.__whenToBreakMs:
					self.__initiateBreak()
		elif data[7] == "1":
			self.__logData("Battle LOST!")
			self.myTurn = False
			self.__playerInfo.battle = False
			self.wildPokemon = None
		else:
			self.myTurn = True

	def __handleMapChange(self):
		# Sending map change messages, sleeping for good measure
		self.__sendB74()
		time.sleep(0.3)
		if self.__playerInfo.isPlayerInWater():
			self.__changeMount("surf")
		elif (self.__playerInfo.getItemIndex("Bike") != -1 and not self.__playerInfo.battle):
			self.__changeMount("Bike")
		time.sleep(0.1)
		self.__players = dict()
		self.playersSignal.emit(self.__players)
		self.__sendB5()
		time.sleep(0.3)
		self.__sendB55()

		# Reset map change update xy timer
		self.__updateXYTimerMap.stop()
		self.__updateXYTimerMap.start()

	def __handleMapUpdate(self, data):
		raw_rock_data = data.split("`")[8]
		if len(raw_rock_data) > 0:
			raw_rock_data = raw_rock_data.replace("[[", "[").replace("]]", "]").replace("],[", "], [").split(", ")

			rocks = []
			self.__rocks = dict()

			for rock in raw_rock_data:
				rock = rock.replace(rock.split(",")[2], "'" + rock.split(",")[2] + "'")
				rock_list = ast.literal_eval(rock)
				rocks.append(rock_list)
				self.__rocks[str(rock_list[0])+","+str(rock_list[1])] = rock_list

			if len(rocks) > 0:
				self.rockSignal.emit(rocks)

	def __handleMiningRockDepleted(self, data):
		split_string = data.split('`')
		rock_key = split_string[4] + "," + split_string[5]
		self.__rocks[rock_key][3] = 0

		self.rockSignal.emit(self.__rocks.values())
		if self.__playerInfo.mining and rock_key == self.__playerInfo.currentRock:
			self.__playerInfo.mining = False
			self.__sendStopMineAnimation()
			self.__miningTimer.stop()
			self.__playerInfo.currentRock = ''

	def __handleMiningRockRestored(self, data):
		split_string = data.split('`')
		rock_key = split_string[4] + "," + split_string[5]
		self.__rocks[rock_key][3] = 1
		self.rockSignal.emit(self.__rocks.values())

	def handlePokemonReorder(self, move_from, move_to):
		''' Reorder pokemon.

			Changes the order of pokemon team.
		'''
		if not self.__playerInfo.battle and not self.__running:
			temp_pokemon = self.__playerInfo.team[move_to - 1]

			self.__playerInfo.team[move_to - 1] = self.__playerInfo.team[move_from]
			self.__playerInfo.team[move_from] = temp_pokemon

			self.teamSignal.emit(self.__playerInfo.team)

			self.__sendB2(move_from, move_to)

			if move_from == 0 or move_to == 1:
				response_timer = Timer(random.uniform(0.3,0.8), self.__sendB75)
				response_timer.setDaemon(True)
				response_timer.start()

			if not self.__playerInfo.setActivePokemon():
				self.__logData("<font color='red'>ERROR: All pokemon seem to be fainted.</font>")
				self.disconnect()
		else:
			self.__logData("<font color='red'>ERROR: To reorder pokemon you must first stop the bot and finish all active battles.</font>")

	def sendPmsg(self, player, message):
		if self.__connected:
			if player == "":
				if "/" == message[3]:
					self.__sendB4(message[4:])
				else:
					self.__sendB66(message)
			elif player == "<cl>":
				self.__sendClanMessage(message)
			else:
				self.__sendR36(player, message)
		else:
			self.__logData("<font color='red'>ERROR: Cannot send messaga. Not connected.</font>")

	def __processPmsg(self, message):
		split_string = message.split('`')
		uer_type = split_string[4][:3]
		category = split_string[4][3:6]
		msg = split_string[4][6:]
		user = split_string[5]
		if category == "<l>":
			location = msg[msg.find("<")+1:msg.find(">")]
			if location == self.__playerInfo.cleanMapName:
				self.chatSignal.emit(uer_type, category, user, msg)
		else:
			self.chatSignal.emit(uer_type, category, user, msg)

	def __handleClanMessage(self, message):
		split_string = message.split('`')
		uer_type = split_string[4][:3]
		msg = split_string[4][3:]
		user = split_string[5]
		self.chatSignal.emit(uer_type, "<cl>", user, msg)

	def __sendClanMessage(self, message):
		self.__sendXtMessage("b67", [message])

	def __processR36(self, message):
		split_string = message.split('`')

		user = split_string[4]
		category = split_string[5][0:3]
		uer_type = split_string[5][:3]
		msg = split_string[5][3:]
		self.chatSignal.emit(uer_type, "<f>", user, msg)

		pm_settings = self.__botRules.pmNotifications()
		self.__notificationHandler.handleNotification("pm",pm_settings[0] , pm_settings[1])

		if user.lower() not in self.__pmNames.keys():
			self.__pmNames[user.lower()] = 1
			#self.__smartResponse(user.lower(), msg)
		else:
			self.__pmNames[user.lower()] += 1

	def __smartResponse(self, user, message):
		""" Replies to a PM.

			Generate a reply based keywords detected.
		"""
		print("GOT PM!!")
		#QMessageBox.question(QWidget(), 'Private Message', "[{}]: {}".format(user, message), QMessageBox.Ok)

		# Below is an example of responding to a PM
		# I didn't have time to fully implement this
		# I started with a new widget called socialConfigWidge
		# start from there if you'd like to make this work from GUI
		'''
		response = "ha :p"

		if "bot" in message or "macro" in message:
			response = ":p nope"
		elif message == "hey" or message == "hi":
			response = "hey"
		elif "gz" in message or "congrats" in message:
			response = "thanks!"
		elif "nature" in message:
			response = "idk PC"
		elif "join" in message or "clan" in message or "sell" in message:
			response = "Um.. no thanks!"

		if user == "brody" or user == "anubisius":
			response = "Well well well... if it isn't " + user + " himself... haha"

		response_timer = Timer(7, self.sendPmsg, [user, response])
		response_timer.setDaemon(True)
		response_timer.start()
		'''

	def __sendVersion(self):
		version_msg = ('<msg t=\'sys\'>' + 
					   '<body action=\'verChk\' r=\'0\'>' +
					   '<ver v=\'' + self.__gameVersion + '\' />' +
					   '</body></msg>\x00')
		self.__gameSocket.sendData(version_msg)

	def __sendR(self):
		""" Sends R message

			Seems to be sent when battle is won.
		"""
		self.__sendXtMessage("r", [], header=False)

	def __sendB2(self, move_from, move_to):
		''' Sends a b2 message.

			The b2 message changes the team order.
		'''
		self.__sendXtMessage("b2", [move_from, move_to])

	def __sendB4(self, command):
		""" Sends a B4 message.

			This is a chat command.
		"""
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)


		msg_b4 =("<msg t='xt'><body action='xtReq' r='1'><![CDATA[<dataObj>" +
				 "<var n='name' t='s'>PokemonPlanetExt</var>" +
				 "<var n='cmd' t='s'>b4</var>" +
				 "<obj t='o' o='param'>" +
					 "<var n='command' t='s'>" + command + "</var>" +
					 "<var n='pke' t='s'>" + packet_key_crypto + "</var>" +
					 "<var n='pk' t='s'>" + packet_key + "</var>" +
					 "<var n='te' t='n'>" + play_time + "</var>" +
				 "</obj></dataObj>]]></body></msg>\x00")

		self.__gameSocket.sendData(msg_b4)

	def __sendB5(self):
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

		msg_b5 =  ('<msg t=\'xt\'>' +
						'<body action=\'xtReq\' r=\'1\'>' +
							'<![CDATA[<dataObj>' +
								'<var n=\'name\' t=\'s\'>PokemonPlanetExt</var>' +
								'<var n=\'cmd\' t=\'s\'>b5</var>' +
								'<obj t=\'o\' o=\'param\'>' +
									'<var n=\'y\' t=\'n\'>' + str(self.__playerInfo.getY()) + '</var>' +
									'<var n=\'x\' t=\'n\'>' + str(self.__playerInfo.getX()) + '</var>' +
									'<var n=\'map\' t=\'s\'>' + self.__playerInfo.cleanMapName + '</var>' +
									'<var n=\'pke\' t=\'s\'>' + packet_key_crypto + '</var>' +
									'<var n=\'pk\' t=\'s\'>' + packet_key + '</var>' +
									'<var n=\'te\' t=\'n\'>' + play_time + '</var>' +
								'</obj>' +
							'</dataObj>]]>' +
						'</body>' +
					'</msg>\x00')

		self.__gameSocket.sendData(msg_b5)

	def __sendB17(self):
		""" Sends a B17 message.

			This is to decline a trade.
		"""
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

		msg_b17 = ("<msg t='xt'> <body action='xtReq' r='1'> <![CDATA[<dataObj>" +
				   "<var n='name' t='s'>PokemonPlanetExt</var>" +
				   "<var n='cmd' t='s'>b17</var>" +
				   "<obj t='o' o='param'>" +
						"<var n='pke' t='s'>" + packet_key_crypto + "</var>" +
						"<var n='pk' t='s'>" + packet_key + "</var>"
						"<var n='te' t='n'>" + play_time + "</var>"
				   "</obj></dataObj>]]></body></msg>\x00")

		if self.botWatch:
			self.__generateFakeMouseClick(9)

		self.__gameSocket.sendData(msg_b17)

		self.__playerInfo.busy = False

	def __sendB55(self):
		mount ='0' if self.__playerInfo.moveType == '' else self.__playerInfo.moveType.title()

		segments = [self.__playerInfo.getX(), self.__playerInfo.getY(), 
					self.__playerInfo.direction, self.__playerInfo.moveType, 
					self.__playerInfo.getMap(), self.__playerInfo.fishing, mount]
					
		self.__sendXtMessage("b55", segments)

	def __sendB56(self, data):
		player_name = str(data[4]).lower()

		offset = 0 if not self.__playerInfo.moving else 64 - self.__playerInfo.mapMovements
		mount = 0 if self.__playerInfo.mount == '' else self.__playerInfo.mount

		segments = [self.__playerInfo.getX(), self.__playerInfo.getY(), 
					self.__playerInfo.direction, self.__playerInfo.moveType, 
					player_name, offset, self.__playerInfo.fishing, mount]

		self.__sendXtMessage("b56", segments)

	def __sendB61(self):
		''' Sends a B61 message

			This is a game login message
		'''
		self.__sendXtMessage("b61", [self.__webSession.getHashPassword(), self.__webSession.getId(), 3])

	def __sendB66(self, message):
		""" Sends message B66.

			This is a chat message.
		"""
		self.__sendXtMessage("b66", [message])

	def __sendB74(self):
		''' Sends a B74 message

			I forget what this does...
		'''
		self.__sendXtMessage("b74", [self.__webSession.getUsername()])

	def __sendB75(self):
		''' Sends a b75 message.

			The b75 message changes the follow pokemon sprite.
		'''
		self.__sendXtMessage("b75", [self.__playerInfo.team[0].id])

	def __sendB191(self, mount):
		""" Sends a B191 message.
			
			This is a mount update message.
		"""
		self.__sendXtMessage("b191", [mount], header=False)

	def __sendR8(self):
		x = str(self.__playerInfo.getX())
		y = str(self.__playerInfo.getY())
		x_crypto = stringToMd5(x + self.__key1 + self.__playerInfo.getUsername())
		y_crypto = stringToMd5(y + self.__key1 + self.__playerInfo.getUsername())

		segments = [x, y, x_crypto, y_crypto, 0, self.__playerInfo.cleanMapName]
		self.__sendXtMessage("r8", segments, header=False)

	def __sendR36(self, player, message):
		""" Sends a R36 message.

			This is a prive message.
		"""
		self.__sendXtMessage("r36", [player, message])

	def __sendB0(self, moveIndex):
		""" Sends a B0 message.

			B0 Message is sent when learning a move.
		"""
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

		msg_b0 =   ("<msg t='xt'>" +
					"<body action='xtReq' r='1'>" +
					"<![CDATA[<dataObj>" +
						"<var n='name' t='s'>PokemonPlanetExt</var>" +
						"<var n='cmd' t='s'>b0</var>" +
						"<obj t='o' o='param'>" +
							"<var n='moveNum' t='n'>" + str(moveIndex) + "</var>" +
								"<var n='pke' t='s'>" + packet_key_crypto + "</var>" +
								"<var n='pk' t='s'>" + packet_key + "</var>" +
								"<var n='te' t='n'>" + play_time + "</var>" +
							"</obj>" +
					"</dataObj>]]>" +
					"</body>" +
					"</msg>\x00")

		self.__gameSocket.sendData(msg_b0)


	def __sendB11(self, pokemonIndex, itemName):
		""" Sends a B11 message.

			B11 Message is sent when using an item.
			No data verification is done at this point.
			Meaning whatever is passed in will be sent.
		"""
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

		msg_b11 =  ('<msg t=\'xt\'>' +
					'<body action=\'xtReq\' r=\'1\'>' +
					'<![CDATA[<dataObj>' +
						'<var n=\'name\' t=\'s\'>PokemonPlanetExt</var>' +
						'<var n=\'cmd\' t=\'s\'>b11</var>' +
						'<obj t=\'o\' o=\'param\'>' +
							'<var n=\'i\' t=\'s\'>' + itemName + '</var>' +
							'<var n=\'p\' t=\'n\'>' + str(pokemonIndex) + '</var>' +
							'<var n=\'pke\' t=\'s\'>' + packet_key_crypto +'</var>' +
							'<var n=\'pk\' t=\'s\'>' + packet_key + '</var>' +
							'<var n=\'te\' t=\'n\'>' + play_time + '</var>' +
						'</obj>'
					'</dataObj>]]>'
					'</body>'
				'</msg>\x00')

		self.__gameSocket.sendData(msg_b11)

	def __sendB18(self):
		""" Sends a b18 message.

			This message is to confirm evolution of a pokemon.
		"""
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

		msg_b18 =  ("<msg t='xt'>" +
					"<body action='xtReq' r='1'>" +
						"<![CDATA[<dataObj>" +
							"<var n='name' t='s'>PokemonPlanetExt</var>" +
							"<var n='cmd' t='s'>b18</var>" +
							"<obj t='o' o='param'>" +
								"<var n='pke' t='s'>" + packet_key_crypto + "</var>" +
								"<var n='pk' t='s'>" + packet_key + "</var>" +
								"<var n='te' t='n'>" + play_time + "</var>" +
							"</obj>" +
						"</dataObj>]]>" +
					"</body>" +
					"</msg>\x00")

		self.__gameSocket.sendData(msg_b18)


	def __sendB19(self):
		""" Sends a b19 message.

			This message is to deny evolution of a pokemon.
		"""
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

		msg_b19 =  ("<msg t='xt'>" +
					"<body action='xtReq' r='1'>" +
						"<![CDATA[<dataObj>" +
							"<var n='name' t='s'>PokemonPlanetExt</var>" +
							"<var n='cmd' t='s'>b19</var>" +
							"<obj t='o' o='param'>" +
								"<var n='pke' t='s'>" + packet_key_crypto + "</var>" +
								"<var n='pk' t='s'>" + packet_key + "</var>" +
								"<var n='te' t='n'>" + play_time + "</var>" +
							"</obj>" +
						"</dataObj>]]>" +
					"</body>" +
					"</msg>\x00")

		self.__gameSocket.sendData(msg_b19)

	def __sendB26(self):
		msg_b26 =  ('<msg t=\'xt\'>' +
				   		'<body action=\'xtReq\' r=\'1\'>' +
					   		'<![CDATA[<dataObj>' +
						   		'<var n=\'name\' t=\'s\'>PokemonPlanetExt</var>' +
						   		'<var n=\'cmd\' t=\'s\'>b26</var>' +
						   		'<obj t=\'o\' o=\'param\'></obj>' +
					   		'</dataObj>]]>' +
				   		'</body>' +
				   	'</msg>\x00')

		self.__gameSocket.sendData(msg_b26)

	def __sendB38(self):
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

		msg_b38 =  ("<msg t='xt'>" +
					"<body action='xtReq' r='1'>" +
					"<![CDATA[<dataObj>" +
						"<var n='name' t='s'>PokemonPlanetExt</var>" +
						"<var n='cmd' t='s'>b38</var>" +
						"<obj t='o' o='param'>" +
							"<var n='pke' t='s'>" + packet_key_crypto +"</var>" +
							"<var n='pk' t='s'>" + packet_key +"</var>" +
							"<var n='te' t='n'>" + play_time +"</var>" +
						"</obj>" +
					"</dataObj>]]>" +
					"</body>" +
					"</msg>\x00")

		self.__gameSocket.sendData(msg_b38)

	def __sendB70(self, rod = "Old Rod"):
		""" Send a B70 message
			
			This is starts fishing with specified rod.
		"""
		self.__sendXtMessage("b70", [rod])


	def __sendB76(self, moveSlot = 0, command = "z", param = "z"):
		""" Compose and send a battle MOVE message"""
		self.__sendXtMessage("b76", [moveSlot, command, param])

	def __sendB77(self):
		''' Compose and send a battle RUN message '''
		self.__sendXtMessage("b77", [])

	def __sendB78(self):
		''' Compose and send a wild battle message'''

		# We're busy with a request so wait until it clears
		while self.__playerInfo.busy:
			time.sleep(0.5)

		encrypted_map = stringToMd5(self.__playerInfo.cleanMapName + "dlod02jhznpd02jdhggyambya8201201nfbmj209ahao8rh2pb" + self.__playerInfo.getUsername());

		segments = [self.__playerInfo.cleanMapName, self.__playerInfo.moveType, encrypted_map]

		self.__sendXtMessage("b78", segments)

	def __sendB122(self):
		# Randomize perfect hook chance
		catch_type = "0"
		if random.randint(1,3) == 3:
			catch_type = "1"

		self.__sendXtMessage("b122", [catch_type])

	def __sendB163(self, x, y, pickaxe = "Old Pickaxe"):
		""" Send a B163 message
			
			This is starts mining with specified pickaxe.
		"""
		self.__sendXtMessage("b163", [pickaxe, x ,y])

	def __sendFishAnimation(self):
		''' Sends fish animation message

			Shows the user as fishing to others.
		'''
		self.__sendXtMessage("f", [self.__playerInfo.direction[0:1]], header=False)

	def __sendMineAnimation(self):
		''' Sends mine animation message

			Shows the user as mining to others.
		'''
		self.__sendXtMessage("f2", [self.__playerInfo.direction[0:1]], header=False)

	def __sendStopMineAnimation(self):
		''' Sends stop mine animation message

			Shows the user as standing to others.
		'''
		self.__sendXtMessage("f3", [self.__playerInfo.direction[0:1]], header=False)

	def __changeMount(self, mount):
		''' Changes the players mount.

			Sends the B119 message to set the mount.
			This needs to be sent every time map is changed as well.
		'''

		if self.__playerInfo.mount != mount:
			self.__logData("<b> Changing mount to "+ mount +"</b>")

		self.__playerInfo.moveType = mount.lower()
		self.__playerInfo.mount = mount

		# If we're dismounting
		if mount == "":
			self.__logData("<b>Dismounting</b>")
			self.__sendB191("0")
		else:
			self.__sendB191(mount)

		self.mountChanged.emit(mount)

	def __sendMove(self):
		''' Send a player move message

			Sends a move message with appropriate mount
		'''

		mount_flag = ''

		if self.__playerInfo.moveType.lower() == "bike":
			mount_flag =  "b"
		elif self.__playerInfo.moveType.lower() == "surf":
			if self.__playerInfo.movementSpeed >= 16:
				mount_flag = "z"
			else:
				mount_flag = "s"

		# We're busy with a request so wait until it clears
		while self.__playerInfo.busy:
			time.sleep(0.5)

		self.__sendXtMessage("m", [self.__playerInfo.direction[0:1], mount_flag], header=False)


	def __checkForBattle(self):
		""" Check for wild batte

			Checks if a battle should be issued and sends the command.
		"""

		start_battle = False

		if self.__playerInfo.battleTile(self.__playerInfo.getX(), self.__playerInfo.getY()):
			if self.__playerInfo.haveUsablePokemon():
				ability_id = self.__playerInfo.team[0].ability.id

				if (ability_id == 1 or ability_id == 73 or ability_id == 95):
					if random.randint(1, 14) == 7:
						start_battle = True

				elif ability_id == 35 or ability_id == 71:
					if random.randint(1, 9) <= 2:
						start_battle = True

				elif ability_id == 99:
					if random.randint(1, 90) <= 15:
						start_battle = True

				elif random.randint(1, 9) == 7:
					start_battle = True

		if start_battle:
			self.__sendB78()
			self.__playerInfo.battle = True


	def setRules(self, selectedTiles, rules):
		""" Set botting rules

			Sets which tiles can be walked on and rules to be followed.
			Starts the main bot loop.
		"""
		if self.__connected:

			if self.__main_bot_thread is not None:
				if self.__main_bot_thread.isAlive():
					self.__logData("<font color='red'>ERROR: Previous bot action has not finished. Wait for it to finish or restart the bot!</font>")
					return
			# Backup tiles for when reconnecting
			if self.__selectedTiles == None:
				self.__selectedTiles = selectedTiles
			if self.__playerInfo.setSelectedTiles(selectedTiles) or rules.mode != "Battle":
				self.__botRules = rules
				self.__running = True
				self.runningSignal.emit(True)
				self.__main_bot_thread = Thread(target=self.botLoop, name="Bot Loop Thread")
				self.__main_bot_thread.setDaemon(True)
				self.__main_bot_thread.start()
			else:
				self.__logData("<font color='red'>ERROR: Battle mode requires at least 4 tiles to be selected!</font>")
				self.runningSignal.emit(False)
		else:
			self.__logData("<font color='red'>ERROR: Cannot set selected tiles, not logged in.</font>")
			self.runningSignal.emit(False)

	def stopBotting(self):
		self.__running = False
		self.runningSignal.emit(False)
		self.hook = False
		self.__playerInfo.fishing = 0
		self.__playerInfo.mining = False
		self.__playerInfo.currentRock = ''
		if self.__fishingTimer.is_running:
			self.__fishingTimer.stop()
		if self.__miningTimer.is_running:
			self.__miningTimer.stop()

	def walkCommand(self, directions):
		if not self.__playerInfo.moving and not self.__running:
			self.__walk_thread = Thread(target=self.walkLoop, args=(directions,), name="Walk Thread")
			self.__walk_thread.setDaemon(True)
			self.__walk_thread.start()

	def walkLoop(self, directions):
		if self.__connected and not self.__running:
			while self.__playerInfo.battle:
				if self.__checkHealDuringBattle():
					self.__randomizedSleep("battlestep")
					continue
				self.__smartAttack()
				self.__randomizedSleep("battlestep")

			self.__playerInfo.moving = True
			for step in directions:
				direction = self.__playerInfo.directionOfTile(step[1], step[0])
				moved = self.__playerInfo.moved(direction, False)
				if moved:
					self.__sendMove()
					self.__sendFakeKeyLog(direction)
					self.positionSignal.emit(self.__playerInfo.cleanMapName, self.__playerInfo.getX(), self.__playerInfo.getY(), self.__playerInfo.direction,  False)
					self.__randomizedSleep("walk")

					if self.__playerInfo.isMapExitTile():
						location = self.__playerInfo.getMapExit()
						if self.__playerInfo.exitMap(location):
							self.positionSignal.emit(location[0], location[1], location[2], self.__playerInfo.direction, False)
							self.__handleMapChange()
						else:
							self.__logData("<font color='red'>ERROR: No map file for: <b>{}</b></font>".format(location[0]))
						break
				else:
					break
			self.__playerInfo.moving = False


	def botLoop(self):
		# Directions we moved in last, give it priority
		last_direction = "DOWN"

		# True when we need to resend the fishing message
		resend_fishing = False

		while self.__connected and self.__running and self.__playerInfo.haveUsablePokemon():
			# Not in battle yet
			if not self.__playerInfo.battle and not self.__playerInfo.busy:
				if self.battleWon:
					self.__randomizedSleep("battleend")
					self.__sendR()
					self.battleWon = False

				if self.__checkHealOutsideBattle():
					continue
				# Battle mode
				if self.__botRules.mode == "Battle":
					moved = False
					direction = None
					while not moved:
						if random.randint(0,10) < 8:
							direction = last_direction
						else:
							moves = self.__playerInfo.getWalkableDirections(bounded=True)
							if len(moves) > 1:
								direction = moves[random.randint(0,len(moves)-1)]
							else:
								direction = moves[0]

						moved = self.__playerInfo.moved(direction, True)

					# Direction changed so simulate a key up
					if direction != last_direction:
						# Send the key we would have released
						self.__sendFakeKeyLog(last_direction)

					last_direction = direction
					self.__randomClick()
					self.__sendMove()
					self.positionSignal.emit(self.__playerInfo.cleanMapName, self.__playerInfo.getX(), self.__playerInfo.getY(), self.__playerInfo.direction,  False)
					self.__checkForBattle()
					self.__randomizedSleep("move")
				# Fishing mode
				elif self.__botRules.mode == "Fish":
					if self.__playerInfo.isPlayerNearWater() and self.__playerInfo.faceWater():
						self.positionSignal.emit(self.__playerInfo.cleanMapName, 
												 self.__playerInfo.getX(), 
												 self.__playerInfo.getY(), 
												 self.__playerInfo.direction,
												 False)
						interval = 2.1 - (self.__playerInfo.fishingLevel * 0.01)
						if self.__botRules.fastFish():
							interval = 2.1 - ((self.__playerInfo.fishingLevel * 2.0) * 0.01)
						if self.__playerInfo.fishing == 0 and not self.__fishingTimer.is_running and not self.hook:
								rod = self.__playerInfo.getBestFishingRod()
								if rod != None:
									if self.__fishingTimer.is_running:
										self.__fishingTimer.stop()
									self.__fishingTimer = RepeatTimer(interval, self.__sendB70, rod)
									self.__fishingTimer.start()
									self.__sendB70(rod)
									self.__sendFishAnimation()
									self.__logData("<b>Casting using: " + rod + "</b>")
									self.__playerInfo.fishing = 1
								else:
									self.__logData("<font color='red'>STOP! Can't fish, no usable rod!</font>")
									self.stopBotting()
						elif resend_fishing:
							rod = self.__playerInfo.getBestFishingRod()
							if self.__fishingTimer.is_running:
								self.__fishingTimer.stop()
							self.__fishingTimer = RepeatTimer(interval, self.__sendB70, rod)
							self.__fishingTimer.start()
							self.__sendB70(rod)
							resend_fishing = False
						elif self.__playerInfo.fishing == 1 and self.hook:
							failed = random.randint(1,50) == 10
							if not failed:
								self.__randomizedSleep("fish")
								self.__logData("<b>Succesfully hooked a pokemon!</b>")
								self.__sendB122()
								self.hook = False
								resend_fishing = True
							else:
								self.__logData("<b>Failed to hook a pokemon!</b>")
								self.__fishingTimer.stop()
								self.hook = False
								self.__playerInfo.fishing = 0
								self.__randomizedSleep("fish") 
							self.__sendFakeKeyLog("SPACE")

						self.__randomizedSleep("battlestep")
					else:
						self.__logData("<font color='red'>STOP! Can't fish, not facing a water tile!</font>")
						self.stopBotting()
				elif self.__botRules.mode == "Mine":
					if self.__playerInfo.isPlayerNearRock(self.__rocks):
						if not self.__playerInfo.mining  and not self.__miningTimer.is_running:
							current_direction = self.__playerInfo.direction.upper()
							rock_coords = self.__playerInfo.faceAvailableRock(self.__rocks)
							if rock_coords[0] is not "NONE":
								if self.botWatch:
									if current_direction != rock_coords[0]:
										self.__sendFakeKeyLog(rock_coords[0])
										self.__randomizedSleep("botwatch")
									self.__sendFakeKeyLog("SPACE")

								best_pickaxe = self.__playerInfo.getBestPickaxe()
								if best_pickaxe is not None:
									self.__sendMineAnimation()
									interval = 2.5 - (self.__playerInfo.miningLevel * 0.012)
									if self.__botRules.fastMine():
										interval = 2.5 - ((self.__playerInfo.miningLevel * 1.9) * 0.012)
									if self.__miningTimer.is_running:
										self.__miningTimer.stop()
									self.__miningTimer = RepeatTimer(interval, self.__sendB163, rock_coords[1], rock_coords[2], best_pickaxe)
									self.__miningTimer.start()
									self.__playerInfo.mining = True
									self.positionSignal.emit(self.__playerInfo.cleanMapName, self.__playerInfo.getX(), self.__playerInfo.getY(), self.__playerInfo.direction,  False)
									self.__logData("<b>Mining using: " + best_pickaxe + "</b>")
								else:
									self.__logData("<font color='red'>STOP! Can't mine, no pickaxe!</font>")
									self.stopBotting()
						self.__randomizedSleep("battlestep")
					else:
						self.__logData("<font color='red'>STOP! Can't mine, not near a rock!</font>")
						self.stopBotting()
			# In battle and its my turn
			elif self.__playerInfo.battle and self.myTurn and not self.__playerInfo.busy:

				# Only heal if we're not running away
				if (self.__checkHealDuringBattle() and
				   (self.__botRules.canBattle(self.wildPokemon) or 
				    self.__botRules.hasCatchRule(self.wildPokemon))):
					self.__randomizedSleep("battlestep")
					continue

				if self.__botRules.canBattle(self.wildPokemon):
					self.__randomizedSleep("battlestep")
					self.__smartAttack()
					self.myTurn = False
				elif self.__botRules.hasCatchRule(self.wildPokemon):
					self.__randomizedSleep("battlestep")
					self.__handleCatching()
					self.myTurn = False
				elif (self.wildPokemon.name in self.__botRules.avoid or 
					 (self.wildPokemon.elite and self.__botRules.avoidElite)):
					self.__randomizedSleep("battlestep")
					if self.botWatch:
						self.__sendFakeKeyLog("4")
					self.__sendB77()
					self.myTurn = False
					self.__playerInfo.battle = False
					self.__randomizedSleep("battleend")
					self.__logData("Running away from battle!")
				else:
					self.__logData("<font color='red'>STOP! Pokemon in catch list!</font>")
					self.stopBotting()
			else:
				time.sleep(0.1)

		self.stopBotting()

	def __handleCatching(self):
		''' Handle catching wild pokemon.

			Performs steps specified by catching rule to catch a wild pokemon.
		'''
		# Get the catch rule for this wild pokemon
		rule = self.__botRules.getCatchRule(self.wildPokemon)

		if rule != None and not rule.stop:
			# If catching pokemon is dead hen stop and let the user do it manually.
			if self.__playerInfo.team[rule.pokemon].currentHealth < 1:
				self.__logData("<font color='red'>STOP! CATCHING POKEMON IS DEAD!</font>")
				self.disconnect()
				return
			# Swap pokemon.
			if self.__playerInfo.activePokemon != rule.pokemon:
				if self.botWatch:
					self.__sendFakeKeyLog("3")
					self.__randomizedSleep("botwatch")
					self.__generateFakeMouseClick(rule.pokemon + 1)
				self.__sendB76(command="switchPokemon", param=str(rule.pokemon))
				self.__logData("<font color='red'>Switching pokemon to <b>{}</b>!</font>".format(self.__playerInfo.team[rule.pokemon].name))
				self.__playerInfo.activePokemon = rule.pokemon
			# Send attack
			elif self.wildPokemon.getHpPercent() > rule.health:
				if self.botWatch:
					self.__sendFakeKeyLog("1");
					self.__randomizedSleep("botwatch");
					self.__sendFakeKeyLog(str(rule.move) + 1);
				self.__sendB76(moveSlot=rule.move)
			# Try to catch
			elif self.wildPokemon.getHpPercent() <= rule.health:
				if rule.status == "none" or rule.status == self.wildPokemon.ailment:
					if self.__playerInfo.getCatchingPokeball(rule.pokeball) != -1:
						if self.botWatch:
							item_index = self.__playerInfo.getBattleItems().index(rule.pokeball)
							current_item_index = 0
							while current_item_index < item_index:
								self.__generateFakeMouseClick(7)
								self.__randomizedSleep("botwatch")
								current_item_index += 1

							self.__generateFakeMouseClick(8)
						self.__logData("<font color='red'>Throwing a <b>" + rule.pokeball + "</b> to catch <b>" + self.wildPokemon.name + "</b>!</font>")
						self.__sendB76(command="i", param=str(self.__playerInfo.getCatchingPokeball(rule.pokeball)))
					else:
						self.__logData("<font color='red'>STOP! No " + rule.pokeball + " available to catch: " + self.wildPokemon.name +"</font>")
						self.disconnect()
				else:
					if self.botWatch:
						self.__sendFakeKeyLog("1");
						self.__randomizedSleep("botwatch");
						self.__sendFakeKeyLog(str(rule.move) + 1);
					self.__sendB76(moveSlot=rule.move)
		elif rule.stop:
			self.__logData("<font color='red'>STOP! Pokemon with a stop rule encountered!</font>")
			if self.__botRules.stopCatchLogout():
				self.disconnect()
			else:
				self.stopBotting()
		else:
			self.__logData("<font color='red'>STOP! CATCH RULE ERROR!</font>")
			self.disconnect()

	def __smartAttack(self):
		''' Sends an attack during pokemon battle

			Chooses best suited attack based on type and move power
		'''

		# Check again that we are in battle before sending an attack
		if self.wildPokemon == None or self.wildPokemon.currentHp == 0:
			self.__playerInfo.battle = False
			self.myTurn = False
			return

		my_pokemon = self.__playerInfo.team[self.__playerInfo.activePokemon]

		# Moves that should be avoided, they cause recoil or don't kill the oponent.
		avoid_moves = ["False Swipe", "Dream Eater", "Double Edge", "Brave Bird", 
					   "Flare Blitz", "Head Charge", "Head Smash", "Light Of Ruin", 
					   "Shadow End", "Steel Beam", "Struggle", "Submission", "Take Down", 
					   "Volt Tackle", "Wild Charge", "Wood Hammer"]
		highest_power = 0
		highest_effect = 0
		best_move = 0

		for move in my_pokemon.moves:
			# Can't use water move on pokemon with Dry Skin ability
			if (not (self.wildPokemon.ability.name == "Dry Skin" and move.type.name == "Water") and
			    not (self.wildPokemon.ability.name == "Sap Sipper" and move.type.name == "Grass") and
			    not (self.wildPokemon.ability.name == "Lightning Rod" and move.type.name == "Electric") and
			    not (self.wildPokemon.ability.name == "Levitate" and move.type.name == "Ground") and
			    not move.name in avoid_moves and move.accuracy >= 85):
				effect = self.wildPokemon.getEffectiveness(int(move.type.id))
				power = move.power
				# Night shade does damage = pokemon level. This is a rough estimate of power.
				if move.name == "Night Shade":
					power = my_pokemon.level / 3
				if effect * power >= highest_power:
					highest_power = effect * power
					highest_effect = effect
					best_move = move

		if self.botWatch:
			self.__sendFakeKeyLog("1");
			self.__randomizedSleep("botwatch");
			self.__sendFakeKeyLog(str(my_pokemon.moves.index(best_move) + 1));

		self.__logData("<font color='green'>Using: <b>[{}]</b> with effectiveness of: <b>[{}]</b></font>".format(best_move.name, str(highest_effect)))
		self.__sendB76(my_pokemon.moves.index(best_move))

	def __checkHealDuringBattle(self):
		""" Check if pokemon should be healed during battle.

			Looks at the active pokemon and if it needs to be healed
			uses the best possible potion on it. Returns True if a 
			potion was used.
		"""

		# Get active pokemon hp 
		poke_hp = self.__playerInfo.team[self.__playerInfo.activePokemon].getHpPercent()

		# Determine heal threshold. Higher for elite pokemon.
		heal_threshold = 0.25

		if self.__botRules is not None:
			heal_threshold = self.__botRules.healThreshold
		if self.wildPokemon.elite:
			heal_threshold = 0.50

		# This pokemon is dead swap to next usable
		if self.__playerInfo.team[self.__playerInfo.activePokemon].currentHealth < 1:
			next_active = self.__playerInfo.getNextAlivePokemon()
			if next_active != -1:
				if self.botWatch:
					self.__randomizedSleep("battlestep")
					self.__sendFakeKeyLog("3")
					self.__randomizedSleep("botwatch")
					self.__generateFakeMouseClick(next_active + 1)
				self.__sendB76(command="switchPokemon", param=str(next_active))
				self.__logData("<font color='red'>Switching pokemon to <b>{}</b>!</font>".format(self.__playerInfo.team[next_active].name))
				self.__playerInfo.activePokemon = next_active
				return True
			else:
				# No usable pokemon for now we just disconnect
				self.disconnect()
		elif poke_hp <= heal_threshold and self.__playerInfo.getBestPotion() != None:
			if self.botWatch:
				self.__randomizedSleep("battlestep")
				item_index = self.__playerInfo.getBattleItems().index(self.__playerInfo.getBestPotion())
				current_item_index = 0
				while current_item_index < item_index:
					self.__generateFakeMouseClick(7)
					self.__randomizedSleep("botwatch")
					current_item_index += 1

				self.__generateFakeMouseClick(8)

			self.__logData("<b>Using a " + self.__playerInfo.getBestPotion() + " on " + self.__playerInfo.team[self.__playerInfo.activePokemon].name + ".</b>")
			self.__sendB76(command="i", param=str(self.__playerInfo.getItemIndex(self.__playerInfo.getBestPotion())))
			return True

		return False

	def __checkHealOutsideBattle(self):
		for pokemon in range(len(self.__playerInfo.team)):
			poke_hp = self.__playerInfo.team[pokemon].getHpPercent()

			# Item used flags
			potion_used = False
			revive_used = False

			# Default heal threshold based on bot rules set by user
			hp_threshold = self.__botRules.healThreshold

			# If pokemon isn't first in team then its a catching pokemon
			# set a stricter threshold.
			if pokemon != 0 and pokemon in self.__botRules.getUsedPokemon():
				hp_threshold = 0.95

			# Pokemon is dead.
			if self.__playerInfo.team[pokemon].currentHealth < 1:
				if "Revive" in self.__playerInfo.getInventory():
					if self.botWatch:
						self.__randomizedSleep("botwatch")
						self.__generateFakeMouseClick(self.__playerInfo.getItemIndex("Revive") + 100)
						self.__randomizedSleep("botwatch")
						self.__generateFakeMouseClick(pokemon + 10)
					self.__sendB11(pokemon,"Revive")
					self.__logData("<b>Using a Revive on " + self.__playerInfo.team[pokemon].name + ".</b>")
					revive_used = True
				elif "Max Revive" in self.__playerInfo.getInventory():
					if self.botWatch:
						self.__randomizedSleep("botwatch")
						self.__generateFakeMouseClick(self.__playerInfo.getItemIndex("Max Revive") + 100)
						self.__randomizedSleep("botwatch")
						self.__generateFakeMouseClick(pokemon + 10)
					self.__sendB11(pokemon,"Max Revive")
					self.__logData("<b>Using a Max Revive on " + self.__playerInfo.team[pokemon].name + ".</b>")
					revive_used = True

			if revive_used:
				self.__randomizedSleep("battlestep")
				return revive_used

			# If HP is too low use a potion
			if poke_hp < hp_threshold:
				if "Potion" in self.__playerInfo.getInventory():
					if self.botWatch:
						self.__randomizedSleep("botwatch")
						self.__generateFakeMouseClick(self.__playerInfo.getItemIndex("Potion") + 100)
						self.__randomizedSleep("botwatch")
						self.__generateFakeMouseClick(pokemon + 10)
					self.__sendB11(pokemon,"Potion")
					self.__logData("<b>Using a Potion on " + self.__playerInfo.team[pokemon].name + ".</b>")
					potion_used = True
				elif "Super Potion" in self.__playerInfo.getInventory():
					if self.botWatch:
						self.__randomizedSleep("botwatch")
						self.__generateFakeMouseClick(self.__playerInfo.getItemIndex("Super Potion") + 100)
						self.__randomizedSleep("botwatch")
						self.__generateFakeMouseClick(pokemon + 10)
					self.__sendB11(pokemon,"Super Potion")
					self.__logData("<b>Using a Super Potion on " + self.__playerInfo.team[pokemon].name + ".</b>")
					potion_used = True
				elif "Hyper Potion" in self.__playerInfo.getInventory():
					if self.botWatch:
						self.__randomizedSleep("botwatch")
						self.__generateFakeMouseClick(self.__playerInfo.getItemIndex("Hyper Potion") + 100)
						self.__randomizedSleep("botwatch")
						self.__generateFakeMouseClick(pokemon + 10)
					self.__sendB11(pokemon,"Hyper Potion")
					self.__logData("<b>Using a Hyper Potion on " + self.__playerInfo.team[pokemon].name + ".</b>")
					potion_used = True
				else:
					# We have to stop there are no potions to heal with
					self.__logData("<b>NO POTIONS!.</b>")
				self.__randomizedSleep("battlestep")
				break

		return potion_used
			
	def __randomClick(self):
		''' Generate a random fake click on the game screen

			Sends the fake click to server when bot watch is on.
		'''
		if self.botWatch:
			if random.randint(1,250) == 50:
				x = random.randint(70, 900)
				y = random.randint(70, 550)

				self.__sendFakeMouseClick(x, y)

	def __randomizedSleep(self, action):

		# How long to wait
		sleep_time = 0

		# Speed modifier
		speed_modifier = 1
		if self.__botRules != None:
			speed_modifier = (self.__botRules.speed / 3.0)

		# True when extra sleep is used.
		extra_sleep = random.randint(1,1000) > 999

		if action == "move" or action == "walk":
			if self.__playerInfo.moveType != "bike":
				sleep_time = random.uniform(0.280,0.310)
			else:
				sleep_time = random.uniform(0.155,0.170)
		elif action == "battlestep":
			sleep_time = random.uniform(3.100,5.850) / speed_modifier
		elif action == "battleend":
			sleep_time = random.uniform(1.900,3.200) / speed_modifier
		elif action == "fish":
			sleep_time = random.uniform(0.500,1.700) / speed_modifier
		elif action == "botwatch":
			sleep_time = random.uniform(0.400,2.950) / speed_modifier

		if extra_sleep and action != "fish" and action != "walk":
			self.__logData("Taking a random break...")
			sleep_sec = random.randint(18, 85)
			# When we sleep extra and user stops the bot this still runs
			# Make sure we check every seconds if we're still running
			for sec in range(sleep_sec):
				time.sleep(1)
				if not self.__running:
					return

		time.sleep(sleep_time)

	def __updateXY(self):
		"""Updates the server with player location.

		Called every 8 seconds. Update is sent only if player location
		has changed from what was previously reported.
		"""
		if (self.__playerInfo.getX() != self.__lastX or 
			self.__playerInfo.getY() != self.__lastY):
			# Location has changed so send an update
			self.__lastX = self.__playerInfo.getX()
			self.__lastY = self.__playerInfo.getY()
			self.__sendR8()

	def __sendHeartbeat(self):
		"""Sends a heartbeat to the server at a predetermined rate

		Called in a new thread.
		"""

		# Keep going as long as there is a connection
		while self.__connected:
			# Send the message and wait
			self.__gameSocket.sendData(CONSTANTS.GAME_HEARTBEAT_MSG)
			time.sleep(CONSTANTS.GAME_HEARTBEAT_RATE_SEC)

	def __sendXtMessage(self, msg_id, segments, header=True):
		''' Sends the xt message.

			Combines all message segments and sends the message.
		'''

		# Included in every xt message
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

		xt_msg = ''

		if header:
			xt_msg = '`xt`PokemonPlanetExt`{}`1`{}`{}`{}'.format(msg_id, play_time, packet_key, packet_key_crypto)
		else:
			xt_msg = '`xt`PokemonPlanetExt`{}`1'.format(msg_id)
		for segment in segments:
			xt_msg += '`' + str(segment)

		xt_msg += '`\x00'

		self.__gameSocket.sendData(xt_msg)