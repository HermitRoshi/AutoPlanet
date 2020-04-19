from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

class CONSTANTS():
	# Constants
	MAIN_PAGE_URL  = "https://pokemon-planet.com"
	LOGIN_PAGE_URL = "https://pokemon-planet.com/forums/index.php?action=login2"
	USER_PAGE_URL  = "https://pokemon-planet.com/getUserInfo.php"

	GAME_IP   = '167.114.159.20'
	GAME_PORT = 9339

	MIN_STRING_LENGTH = 5
	MAX_STRING_LENGTH = 20

	MAX_CHAT_LINES = 25

	GAME_MAX_TEAM_SIZE = 6
	GAME_HEARTBEAT_RATE_SEC = 30
	GAME_UPDATEXY_RATE_SEC = 8
	GAME_SAVEDATA_RATE_SEC = 1800
	GAME_HEARTBEAT_MSG 	= '`xt`PokemonPlanetExt`p`1`\x00'
	GAME_POLICY_MSG		= '<policy-file-request/>\x00'
	GAME_RMLIST_MSG     = '<msg t=\'sys\'><body action=\'getRmList\' r=\'-1\'></body></msg>\x00'
	GAME_AUTOJOIN_MSG   = '<msg t=\'sys\'><body action=\'autoJoin\' r=\'-1\'></body></msg>\x00'

	WIDGET_MAP_VIEW_WIDTH = 19
	WIDGET_MAP_VIEW_HEIGHT = 19
	IMG_PLAYER = QImage("./images/player.png")
	IMG_POKEBALL = QImage("./images/pokeball.png")
	IMG_GRASS = QImage("./images/grass.png")
	IMG_INDOOR_FLOOR = QImage("./images/indoorfloor.png")
	IMG_INDOOR_BLOCK = QImage("./images/indoorblock.png")
	IMG_CAVE_FLOOR = QImage("./images/cavefloor.png")
	IMG_CAVE_BLOCK = QImage("./images/caveblock.png")
	IMG_SHORT_GRASS = QImage("./images/shortgrass.png")
	IMG_CUT_TREE = QImage("./images/cuttree.png")
	IMG_WATER = QImage("./images/water.png")
	IMG_NPC = QImage("./images/npc.png")
	IMG_LEDGE_DOWN = QImage("./images/ledgedown.png")
	IMG_LEDGE_RIGHT = QImage("./images/ledgeright.png")
	IMG_LEDGE_LEFT = QImage("./images/ledgeleft.png")
	IMG_EXIT = QImage("./images/exit.png")
	IMG_OUTSIDE_BLOCK = QImage("./images/outsideblock.png")



