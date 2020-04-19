import time
import random

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

from PySide2.QtCore import QObject, Signal

class GameHandler(QObject):
	infoSignal = Signal(int, int)
	teamSignal = Signal(object)
	inventorySignal = Signal(object)
	positionSignal = Signal(str, int, int, bool)
	logSignal = Signal(str)
	chatSignal = Signal(str, str, str)
	connectedSignal = Signal(bool)
	mountChanged = Signal(str)
	historySignal = Signal(int, int, object)

	def __init__(self, gameVersion, key1, key2, sessionCookie, userAgent):
		super(GameHandler, self).__init__()
		self.__gameVersion = gameVersion
		self.__key1 = key1
		self.__key2 = key2
		self.__sessionCookie = sessionCookie
		self.__userAgent = userAgent
		self.__startTimeMillis = getTimeMillis()

		# Handles web login and session
		self.__webSession = WebSession(self.__sessionCookie, self.__userAgent)

		# Socket used for game connection
		self.__gameSocket = ThreadedSocket(CONSTANTS.GAME_IP, 
										   CONSTANTS.GAME_PORT)
		self.__gameSocket.receiveSignal.connect(self.__processInboundData)
		self.__gameSocket.timeoutSignal.connect(self.__catchTimeout)

		# Bot state
		self.__running = False

		# Game connection state
		self.__connected = False

		# Did session time out
		self.__timedOut = False

		# Thread to send the game heartbeat
		self.__heartbeat_thread = Thread(target=self.__sendHeartbeat, name="Heartbeat Thread")
		self.__heartbeat_thread.setDaemon(True)

		# Thread for the main bot loop
		self.__main_bot_thread = None

		# Thread for user issued walk commands
		self.__walk_thread = None

		# Set of rules the bot has to follow includes catch list and such
		self.__botRules = None

		# Dictionary of players that have private messaged the player
		self.__pmNames = dict()

		# Player information 
		self.__playerInfo = PlayerInfo()
		self.__playerInfo.stepsWalkedSignal.connect(self.__sendB38)

		# Information about current wild battle
		self.wildPokemon = None
		self.myTurn = False
		self.battleWon = False
		self.useItem = True
		self.hook = False

		# Last X and Y reported to the server
		self.__lastX = 0
		self.__lastY = 0
		self.__updateXYTimerStart = RepeatTimer(CONSTANTS.GAME_UPDATEXY_RATE_SEC, self.__updateXY)
		self.__updateXYTimerMap = RepeatTimer(CONSTANTS.GAME_UPDATEXY_RATE_SEC, self.__updateXY)
		self.__saveDataTimer = RepeatTimer(CONSTANTS.GAME_SAVEDATA_RATE_SEC, self.__sendB26)
		self.__fishingTimer = RepeatTimer(2.1, self.__sendB70)

		# Session information
		self.__battles = 0
		self.__moneyEarned = 0
		self.__pokemonEncountered = dict()
		self.__username = None
		self.__password = None
		self.__selectedTiles = None
		self.__timeoutX = 0
		self.__timeoutY = 0
		self.__backToPosTimer = None
		self.__sendRulesTimer = None

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
		self.__webSession = WebSession(self.__sessionCookie, self.__userAgent)

		# Close the game socket
		self.__gameSocket.close()

		# Reset bot state
		self.__running = False

		# Reset game connection state
		self.__connected = False

		# Socket used for game connection
		self.__gameSocket = ThreadedSocket(CONSTANTS.GAME_IP, 
										   CONSTANTS.GAME_PORT)
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

		# Session information
		self.__battles = 0
		self.__moneyEarned = 0
		self.__pokemonEncountered = dict()

		# Update the display with signals
		self.historySignal.emit(self.__battles, self.__moneyEarned, self.__pokemonEncountered)
		self.connectedSignal.emit(False)
		self.teamSignal.emit(self.__playerInfo.team)
		self.inventorySignal.emit(self.__playerInfo.getInventory())
		self.positionSignal.emit(self.__playerInfo.cleanMapName, self.__playerInfo.getX(), self.__playerInfo.getY(), self.__timedOut)
		self.__logData("You have been logged out.")

		# If we disconnected because of a timeout... reconnect
		if self.__timedOut:
			self.__logData("Attempting to reconnect...")
			self.toggleLogin(self.__username, self.__password)

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
		if path is  not None:
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
				response_timer.start()
			elif message.getMessageAction() == 'b88' and message.getMessageCode() == '-1':
				if self.__playerInfo.isPlayerInWater():
					self.__changeMount("surf")
				response_timer = Timer(0.2, self.__sendB5)
				response_timer.start()
			elif message.getMessageAction() == 'b5' and message.getMessageCode() == '-1':
				self.__sendB55()
				self.__connected = True
				self.__heartbeat_thread.start()
				self.__logData("Connected")
				self.teamSignal.emit(self.__playerInfo.team)
				self.inventorySignal.emit(self.__playerInfo.getInventory())
				self.positionSignal.emit(self.__playerInfo.cleanMapName, self.__playerInfo.getX(), self.__playerInfo.getY(), self.__timedOut)
				self.connectedSignal.emit(True)
				self.infoSignal.emit(self.__playerInfo.money, self.__playerInfo.credits)
				if (self.__playerInfo.getItemIndex("Bike") != -1 and
					self.__playerInfo.moveType != "surf" and not self.__playerInfo.battle):
					self.__changeMount("Bike")
				if self.__timedOut:
					self.__restartBot()
					self.__timedOut = False
			elif message.getMessageAction() == "w2":
				self.__handleNewBattle(message.getMessageRaw())

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
		elif message.getMessageAction() == "ui":
			# Updating inventory and team
			split_string = message.getMessageRaw().split('`')
			self.__playerInfo.updateInventory(split_string[4])
			self.__playerInfo.updateTeam(split_string[5])
			self.teamSignal.emit(self.__playerInfo.team)
			self.inventorySignal.emit(self.__playerInfo.getInventory())
			self.useItem = True
		elif message.getMessageAction() == "r36":
			# Private message
			self.__processR36(message.getMessageRaw())
		elif message.getMessageAction() == "b121":
			# This mean we are prompted to hook a pokemon
			self.__fishingTimer.stop()
			self.hook = True
		elif message.getMessageAction() == "b86":
			# Add an item to inventory
			split_string = message.getMessageRaw().split('`')
			split_string = split_string[4].split(",")
			self.__playerInfo.addItemToInventory(split_string[0], int(split_string[1]))
			self.inventorySignal.emit(self.__playerInfo.getInventory())
		elif message.getMessageAction() == "b87":
			# Remove an item from inventory
			split_string = message.getMessageRaw().split('`')
			split_string = split_string[4].split(",")
			self.__playerInfo.addItemToInventory(split_string[0], -int(split_string[1]))
			self.inventorySignal.emit(self.__playerInfo.getInventory())
		elif message.getMessageAction() == "b185":
			# This is a trade request
			self.__logData("<font color='red'>Denying a trade request!</font>")
			response_timer = Timer(random.randint(2,5), self.__sendB17)
			response_timer.start()

	def __handleAddPlayer(self, data, addBack=False):
		if self.__playerInfo.characterCreated != 0 and addBack:
			self.__sendB56(data)

		player_name = data[4].lower()
		if player_name == "brody" or player_name == "anubisius":
			print("Found Brody or Anubisius")

	def __handleNewBattle(self, data):
		self.wildPokemon = WildPokemon(data)

		self.myTurn = True
		self.__playerInfo.battle = True
		self.__playerInfo.activePokemon = 0
		self.__battles = self.__battles + 1

		name = self.wildPokemon.name
		if(self.wildPokemon.shiny):
			name = "[S]" + name
		elif(self.wildPokemon.elite):
			name = "[E]" + name

		if name in self.__pokemonEncountered.keys():
			self.__pokemonEncountered[name] += 1
		else:
			self.__pokemonEncountered[name] = 1

		self.historySignal.emit(self.__battles, self.__moneyEarned, self.__pokemonEncountered)
		self.__logData("<font color='#3d84a8'><b>Battle! Pokemon:[{}][{}]</b></font>".format(name, self.wildPokemon.level))


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
			if message[3] != "":
				log_message = message[3].title() + "'s " + log_message
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
			self.__playerInfo.activePokemon = 0
		elif data[7] == "1":
			self.__logData("Battle LOST!")
			self.myTurn = False
			self.__playerInfo.battle = False
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
		self.__sendB5()
		time.sleep(0.3)
		self.__sendB55()

		# Reset map change update xy timer
		self.__updateXYTimerMap.stop()
		self.__updateXYTimerMap.start()

	def sendPmsg(self, player, message):
		if player == "":
			if "/pokemon" in message:
				self.__sendB4("pokemon")
			else:
				self.__sendB66(message)
		else:
			self.__sendR36(player, message)

	def __processPmsg(self, message):
		split_string = message.split('`')
		category = split_string[4][3:6]
		msg = split_string[4][6:]
		user = split_string[5]
		if category == "<l>":
			location = msg[msg.find("<")+1:msg.find(">")]
			if location == self.__playerInfo.cleanMapName:
				self.chatSignal.emit(category, user, msg)
		else:
			self.chatSignal.emit(category, user, msg)

	def __processR36(self, message):
		split_string = message.split('`')

		user = split_string[4]
		category = split_string[5][0:3]
		msg = split_string[5][3:]
		self.chatSignal.emit("<f>", user, msg)

		if user.lower() not in self.__pmNames.keys():
			self.__pmNames[user.lower()] = 1
			self.__smartResponse(user.lower(), msg)
		else:
			self.__pmNames[user.lower()] += 1

	def __smartResponse(self, user, message):
		""" Replies to a PM.

			Generate a reply based keywords detected.
		"""
		print("PM'd")

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
		msg_r = "`xt`PokemonPlanetExt`r`1`\x00"
		self.__gameSocket.sendData(msg_r)

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

		self.__gameSocket.sendData(msg_b17)

	def __sendB55(self):
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)
		mount ='0' if self.__playerInfo.moveType == '' else self.__playerInfo.moveType

		msg_b55 = ('`xt`PokemonPlanetExt`b55`1`' + play_time + '`' + packet_key + '`' +
				   packet_key_crypto + '`' + str(self.__playerInfo.getX()) + '`' +
				   str(self.__playerInfo.getY()) + '`' + self.__playerInfo.direction +
				   '`' + self.__playerInfo.moveType + '`' + self.__playerInfo.getMap() +
				   '`' + str(self.__playerInfo.fishing) + '`' + mount + '`\x00')

		self.__gameSocket.sendData(msg_b55)

	def __sendB56(self, data):
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)
		player_name = str(data[4]).lower()

		offset = 0
		if self.__playerInfo.moving:
			offset = 64 - self.__playerInfo.mapMovements

		mount = 0
		if self.__playerInfo.mount != '':
			mount = self.__playerInfo.mount

		msg_b56 = ('`xt`PokemonPlanetExt`b56`1`' + play_time + '`' + packet_key + '`' +
				   packet_key_crypto + '`' + str(self.__playerInfo.getX()) + '`' +
				   str(self.__playerInfo.getY()) + '`' + self.__playerInfo.direction +
				   '`' + self.__playerInfo.moveType + '`' + player_name + '`' + str(offset) +
				   '`' + str(self.__playerInfo.fishing) + '`' + str(mount) + '`\x00')

		self.__gameSocket.sendData(msg_b56)


	def __sendB61(self):
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		random_string = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		key2_hash = stringToMd5(random_string + self.__key2 + play_time)

		msg_b61 = ('`xt`PokemonPlanetExt`b61`1`' + play_time +
                    '`' + random_string + '`' + key2_hash + '`' +
                    self.__webSession.getHashPassword() + '`' +
                    self.__webSession.getId() + '`3`\x00')

		self.__gameSocket.sendData(msg_b61)

	def __sendB66(self, message):
		""" Sends message B66.

			This is a chat message.
		"""
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

		msg_b66 = ('`xt`PokemonPlanetExt`b66`1`' + play_time +
                    '`' + packet_key + '`' + packet_key_crypto + 
                    '`' + message + '`\x00')

		self.__gameSocket.sendData(msg_b66)


	def __sendB74(self):
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

		msg_b74 = ('`xt`PokemonPlanetExt`b74`1`' + play_time +
                    '`' + packet_key + '`' + packet_key_crypto + '`' +
                    self.__webSession.getUsername() + '`\x00')

		self.__gameSocket.sendData(msg_b74)

	def __sendB191(self, mount):
		""" Sends a B191 message.
			
			This is a mount update message.
		"""
		msg_b191 = ('`xt`PokemonPlanetExt`b191`1`' + mount + '`\x00')

		self.__gameSocket.sendData(msg_b191)

	def __sendR8(self):
		x = str(self.__playerInfo.getX())
		y = str(self.__playerInfo.getY())
		x_crypto = stringToMd5(x + self.__key1 + self.__playerInfo.getUsername())
		y_crypto = stringToMd5(y + self.__key1 + self.__playerInfo.getUsername())

		msg_r8 = ('`xt`PokemonPlanetExt`r8`1`' + x + '`' + y + '`' +
				  x_crypto + '`' + y_crypto + '`' + '0' + '`' + self.__playerInfo.cleanMapName + '`\x00')

		self.__gameSocket.sendData(msg_r8)

	def __sendR36(self, player, message):
		""" Sends a R36 message.

			This is a prive message.
		"""

		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

		msg_r36 = ('`xt`PokemonPlanetExt`r36`1`' + play_time +
                    '`' + packet_key + '`' + packet_key_crypto + 
                    '`' + player + '`' + message +'`\x00')

		self.__gameSocket.sendData(msg_r36)

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

		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

		msg_b70 = ('`xt`PokemonPlanetExt`b70`1`' + play_time +
                    '`' + packet_key + '`' + packet_key_crypto + 
                    '`' + rod +'`\x00')

		self.__gameSocket.sendData(msg_b70)


	def __sendB76(self, moveSlot = 0, command = "z", param = "z"):
		""" Compose and send a battle MOVE message"""
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

		msg_b76 = ('`xt`PokemonPlanetExt`b76`1`' + play_time +
                    '`' + packet_key + '`' + packet_key_crypto + '`' +
                    str(moveSlot) + '`' + command + '`' + param +'`\x00')

		self.__gameSocket.sendData(msg_b76)

	def __sendB77(self):
		""" Compose and send a battle RUN message"""

		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

		msg_b77 = ('`xt`PokemonPlanetExt`b77`1`' + play_time +
                    '`' + packet_key + '`' + packet_key_crypto + '`\x00')

		self.__gameSocket.sendData(msg_b77)

	def __sendB78(self):
		""" Compose and send a wild battle message"""

		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)
		encrypted_map = stringToMd5(self.__playerInfo.cleanMapName + "dlod02jhznpd02jdhggyambya8201201nfbmj209ahao8rh2pb" + self.__playerInfo.getUsername());

		msg_b78 = ('`xt`PokemonPlanetExt`b78`1`' + play_time +
                    '`' + packet_key + '`' + packet_key_crypto + '`' +
                    self.__playerInfo.cleanMapName + '`' + self.__playerInfo.moveType + 
                    '`' + encrypted_map +'`\x00')

		self.__gameSocket.sendData(msg_b78)

	def __sendB122(self):
		play_time = str(getTimeMillis() - self.__startTimeMillis)
		packet_key = getRandomString(CONSTANTS.MIN_STRING_LENGTH, CONSTANTS.MAX_STRING_LENGTH)
		packet_key_crypto = stringToMd5(packet_key + self.__key2 + play_time)

		# Randomize perfect hook chance
		catch_type = "0"
		if random.randint(1,3) == 3:
			catch_type = "1"

		msg_b122 = ('`xt`PokemonPlanetExt`b122`1`' + play_time +
                    '`' + packet_key + '`' + packet_key_crypto + 
                    '`' + catch_type +'`\x00')

		self.__gameSocket.sendData(msg_b122)

	def __sendFishAnimation(self):
		direction = self.__playerInfo.direction[0:1]

		msg_fish_animation = "`xt`PokemonPlanetExt`f`1`" + direction + "`\x00"
		self.__gameSocket.sendData(msg_fish_animation)

	def __changeMount(self, mount):
		self.__playerInfo.moveType = mount

		# If we're dismounting
		if mount == "":
			self.__logData("<b>Dismounting</b>")
			self.__sendB191("0")
		else:
			self.__logData("<b> Changing mount to "+ mount +"</b>")
			self.__sendB191(mount)

		self.mountChanged.emit(mount)


	def __sendMove(self):
		""" Compose and send a player movement message """
		direction = self.__playerInfo.direction[0:1]
		msg_move = "`xt`PokemonPlanetExt`m`1`" + direction + "`"

		if self.__playerInfo.moveType == "Bike":
			msg_move = msg_move + "b" + "`\x00"
		elif self.__playerInfo.moveType == "surf":
			if self.__playerInfo.movementSpeed >= 16:
				msg_move = msg_move + "z" + "`\x00"
			else:
				msg_move = msg_move + "s" + "`\x00"
		else:
			msg_move = msg_move + "\x00"

		self.__gameSocket.sendData(msg_move)


	def __checkForBattle(self):
		""" Check for wild batte

			Checks if a battle should be issued and sends the command.
		"""
		if self.__playerInfo.battleTile(self.__playerInfo.getX(), self.__playerInfo.getY()):
			if self.__playerInfo.team[0].currentHealth > 0:
				ability_id = self.__playerInfo.team[0].ability.id

				if (ability_id == 1 or ability_id == 73 or ability_id == 95):
					if random.randint(1, 14) == 7:
						self.__sendB78()

				elif ability_id == 35 or ability_id == 71:
					if random.randint(1, 9) <= 2:
						self.__sendB78()

				elif ability_id == 99:
					if random.randint(1, 90) <= 15:
						self.__sendB78()

				elif random.randint(1, 9) == 7:
					self.__sendB78()


	def setRules(self, selectedTiles, rules):
		""" Set botting rules

			Sets which tiles can be walked on and rules to be followed.
			Starts the main bot loop.
		"""
		if self.__connected:
			# Backup tiles for when reconnecting
			if self.__selectedTiles == None:
				self.__selectedTiles = selectedTiles
			if self.__playerInfo.setSelectedTiles(selectedTiles) or rules.mode != "Battle":
				self.__botRules = rules
				self.__running = True
				self.__main_bot_thread = Thread(target=self.botLoop, name="Bot Loop Thread")
				self.__main_bot_thread.setDaemon(True)
				self.__main_bot_thread.start()
			else:
				self.__logData("<font color='red'>ERROR: Battle mode requires at least 4 tiles to be selected!</font>")
		else:
			self.__logData("<font color='red'>ERROR: Cannot set selected tiles, not logged in.</font>")


	def stopBotting(self):
		self.__running = False
		self.hook = False
		self.__playerInfo.fishing = 0
		if self.__fishingTimer.is_running:
			self.__fishingTimer.stop()

	def walkCommand(self, directions):
		if not self.__playerInfo.moving and not self.__running:
			self.__walk_thread = Thread(target=self.walkLoop, args=(directions,), name="Walk Thread")
			self.__walk_thread.setDaemon(True)
			self.__walk_thread.start()

	def walkLoop(self, directions):
		if self.__connected and not self.__running:
			while self.__playerInfo.battle:
				self.__smartAttack()
				self.__randomizedSleep("battlestep")

			self.__playerInfo.moving = True
			for step in directions:
				direction = self.__playerInfo.directionOfTile(step[1], step[0])
				moved = self.__playerInfo.moved(direction, False)
				if moved:
					self.__sendMove()
					self.positionSignal.emit(self.__playerInfo.cleanMapName, self.__playerInfo.getX(), self.__playerInfo.getY(), False)
					self.__randomizedSleep("walk")

					if self.__playerInfo.isMapExitTile():
						location = self.__playerInfo.getMapExit()
						if self.__playerInfo.exitMap(location):
							self.positionSignal.emit(location[0], location[1], location[2], False)
							self.__handleMapChange()
						else:
							self.__logData("<font color='red'>ERROR: No map file for: <b>{}</b></font>".format(location[0]))
						break

				else:
					break
			self.__playerInfo.moving = False


	def botLoop(self):
		# Directions we can move in
		moves = ["up", "down", "right", "left"]

		while self.__connected and self.__running and self.__playerInfo.activePokemonAlive():

			# Not in battle yet
			if not self.__playerInfo.battle:
				if self.battleWon:
					self.__randomizedSleep("battleend")
					self.__sendR()
					self.battleWon = False

				if self.__checkHealOutsideBattle():
					continue
				# Battle mode
				if self.__botRules.mode == "Battle":
					moved = False
					while not moved:
						moved = self.__playerInfo.moved(moves[random.randint(0,3)], True)
					self.__sendMove()
					self.positionSignal.emit(self.__playerInfo.cleanMapName, self.__playerInfo.getX(), self.__playerInfo.getY(), False)
					self.__checkForBattle()
					self.__randomizedSleep("move")
				# Fishing mode
				elif self.__botRules.mode == "Fish":
					if self.__playerInfo.isPlayerFacingWater():
						if self.__playerInfo.fishing == 1 and not self.__fishingTimer.is_running and not self.hook:
								rod = self.__playerInfo.getBestFishingRod()
								if rod != None:
									interval = 2.1 - (self.__playerInfo.fishingLevel * 0.01)
									self.__fishingTimer = RepeatTimer(interval, self.__sendB70, rod)
									self.__fishingTimer.start()
									self.__sendB70(rod)
									self.__logData("<b>Casting using: " + rod + "</b>")
								else:
									self.__logData("<font color='red'>STOP! Can't fish, no usable rod!</font>")
									self.__running = False
						elif self.__playerInfo.fishing == 1 and self.hook:
							failed = random.randint(1,50) == 10
							if not failed:
								self.__randomizedSleep("fish")
								self.__logData("<b>Succesfully hooked a pokemon!</b>")
								self.__sendB122()
								self.hook = False
							else:
								self.__logData("<b>Failed to hook a pokemon!</b>")
								self.__fishingTimer.stop()
								self.hook = False
								self.__playerInfo.fishing = 0
								self.__randomizedSleep("fish")
						else:
							self.__sendFishAnimation()
							self.__playerInfo.fishing = 1
						self.__randomizedSleep("battlestep")
					else:
						self.__logData("<font color='red'>STOP! Can't fish, not facing a water tile!</font>")
						self.__running = False
			# In battle and its my turn
			elif self.__playerInfo.battle and self.myTurn:
				if self.__checkHealDuringBattle():
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
				elif self.wildPokemon.name in self.__botRules.avoid:
					self.__randomizedSleep("battlestep")
					self.__sendB77()
					self.myTurn = False
					self.__playerInfo.battle = False
					self.__randomizedSleep("battleend")
					self.__logData("Running away from battle!")
				else:
					self.__running = False
					self.__logData("<font color='red'>STOP! Pokemon in catch list!</font>")
			else:
				time.sleep(0.1)

		self.stopBotting()


	def __handleCatching(self):
		rule = self.__botRules.getCatchRule(self.wildPokemon)

		if rule != None and not rule.stop:
			if self.__playerInfo.activePokemon != rule.pokemon:
				self.__sendB76(command="switchPokemon", param=str(rule.pokemon))
				self.__playerInfo.activePokemon = rule.pokemon
			elif self.wildPokemon.getHpPercent() > rule.health:
				self.__sendB76(moveSlot=rule.move)
			elif self.wildPokemon.getHpPercent() <= rule.health:
				if rule.status == "none" or rule.status == wildPokemon.ailment:
					if self.__playerInfo.getItemIndex(rule.pokeball) != -1:
						self.__logData("<font color='red'>Throwing a <b>" + rule.pokeball + "</b> to catch <b>" + self.wildPokemon.name + "</b>!</font>")
						self.__sendB76(command="i", param=str(self.__playerInfo.getItemIndex(rule.pokeball)))
					else:
						self.__logData("<font color='red'>STOP! No " + rule.pokeball + " available to catch: " + self.wildPokemon.name +"</font>")
						self.disconnect()
				else:
					self.__sendB76(moveSlot=rule.move)
		else:
			self.__logData("<font color='red'>STOP! CATCH RULE ERROR!</font>")
			self.disconnect()

	def __smartAttack(self):
		my_pokemon = self.__playerInfo.team[0]
		avoid_moves = ["False Swipe", "Dream Eater"]
		highest_power = 0
		highest_effect = 0
		best_move = 0

		for move in my_pokemon.moves:
			# Can't use water move on pokemon with Dry Skin ability
			if (not (self.wildPokemon.ability.name == "Dry Skin" and move.type.name == "Water") and
			    not (self.wildPokemon.ability.name == "Sap Sipper" and move.type.name == "Grass") and
			    not move.name in avoid_moves):
				effect = self.wildPokemon.getEffectiveness(int(move.type.id))
				power = move.power
				# Night shade does damage = pokemon level. This is a rough estimate of power.
				if move.name == "Night Shade":
					power = my_pokemon.level / 3
				if effect * power > highest_power:
					highest_power = effect * power
					highest_effect = effect
					best_move = move
		self.__logData("<font color='green'>Using: <b>[{}]</b> with effectiveness of: <b>[{}]</b></font>".format(best_move.name, highest_effect))
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
		if self.wildPokemon.elite:
			heal_threshold = 0.50

		# Heal if HP to or drops below 25%
		if poke_hp <= heal_threshold and self.__playerInfo.getBestPotion() != None:
			self.__logData("<b>Using a " + self.__playerInfo.getBestPotion() + " on " + self.__playerInfo.team[self.__playerInfo.activePokemon].name + ".</b>")
			self.__sendB76(command="i", param=str(self.__playerInfo.getItemIndex(self.__playerInfo.getBestPotion())))
			return True

		return False


	def __checkHealOutsideBattle(self):
		for pokemon in self.__botRules.getUsedPokemon():
			if pokemon < len(self.__playerInfo.team):
				poke_hp = self.__playerInfo.team[pokemon].getHpPercent()

				potion_used = False
				# Default heal threshold based on bot rules set by user
				hp_threshold = self.__botRules.healThreshold

				# If pokemon isn't first in team then its a catching pokemon
				# set a stricter threshold.
				if pokemon != 0:
					hp_threshold = 0.95

				# If HP is too low use a potion
				if poke_hp < hp_threshold and self.useItem:
					if "Potion" in self.__playerInfo.getInventory():
						self.__sendB11(pokemon,"Potion")
						self.__logData("<b>Using a Potion on " + self.__playerInfo.team[pokemon].name + ".</b>")
						self.useItem = False
						potion_used = True
					elif "Super Potion" in self.__playerInfo.getInventory():
						self.__sendB11(pokemon,"Super Potion")
						self.__logData("<b>Using a Super Potion on " + self.__playerInfo.team[pokemon].name + ".</b>")
						self.useItem = False
						potion_used = True
					elif "Hyper Potion" in self.__playerInfo.getInventory():
						self.__sendB11(pokemon,"Hyper Potion")
						self.__logData("<b>Using a Hyper Potion on " + self.__playerInfo.team[pokemon].name + ".</b>")
						self.useItem = False
						potion_used = True
					else:
						# We have to stop there are no potions to heal with
						self.__logData("<b>NO POTIONS!.</b>")
						self.useItem = False
					self.__randomizedSleep("battlestep")
					break

		return potion_used
			
	def __randomizedSleep(self, action):

		# True when extra sleep is used.
		extra_sleep = random.randint(1,1000) > 999

		if action == "move" or action == "walk":
			if self.__playerInfo.moveType != "Bike":
				time.sleep(random.uniform(0.260,0.300))
			else:
				time.sleep(random.uniform(0.140,0.165))
		elif action == "battlestep":
			time.sleep(random.uniform(3.100,5.850))
		elif action == "battleend":
			time.sleep(random.uniform(1.900,3.200))
		elif action == "fish":
			time.sleep(random.uniform(0.500,1.700))

		if extra_sleep and action != "fish" and action != "walk":
			self.__logData("Extra sleep...")
			time.sleep(random.uniform(18.555, 37.111))

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