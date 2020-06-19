from PySide2.QtGui import QImage

class CONSTANTS():
	# Constants
	MAIN_PAGE_URL  = "https://pokemon-planet.com"
	LOGIN_PAGE_URL = "https://pokemon-planet.com/forums/index.php?action=login2"
	USER_PAGE_URL  = "https://pokemon-planet.com/getUserInfo.php"

	GAME_IP   = '167.114.159.20'
	GAME_PORT = 9339

	MIN_STRING_LENGTH = 5
	MAX_STRING_LENGTH = 20

	MAX_CHAT_LINES = 500

	GAME_MAX_TEAM_SIZE = 6
	GAME_HEARTBEAT_RATE_SEC = 30
	GAME_UPDATEXY_RATE_SEC = 8
	GAME_SAVEDATA_RATE_SEC = 1800
	GAME_HEARTBEAT_MSG 	= '`xt`PokemonPlanetExt`p`1`\x00'
	GAME_POLICY_MSG		= '<policy-file-request/>\x00'
	GAME_RMLIST_MSG     = '<msg t=\'sys\'><body action=\'getRmList\' r=\'-1\'></body></msg>\x00'
	GAME_AUTOJOIN_MSG   = '<msg t=\'sys\'><body action=\'autoJoin\' r=\'-1\'></body></msg>\x00'

	WIDGET_MAP_VIEW_WIDTH = 21
	WIDGET_MAP_VIEW_HEIGHT = 19
	IMG_PLAYER_RIGHT = QImage("./data/images/player_right.png")
	IMG_PLAYER_LEFT = QImage("./data/images/player_left.png")
	IMG_PLAYER_UP = QImage("./data/images/player_up.png")
	IMG_PLAYER_DOWN = QImage("./data/images/player_down.png")
	IMG_POKEBALL = QImage("./data/images/pokeball.png")
	IMG_GRASS = QImage("./data/images/grass.png")
	IMG_INDOOR_FLOOR = QImage("./data/images/indoorfloor.png")
	IMG_INDOOR_BLOCK = QImage("./data/images/indoorblock.png")
	IMG_CAVE_FLOOR = QImage("./data/images/cavefloor.png")
	IMG_CAVE_BLOCK = QImage("./data/images/caveblock.png")
	IMG_SHORT_GRASS = QImage("./data/images/shortgrass.png")
	IMG_CUT_TREE = QImage("./data/images/cuttree.png")
	IMG_WATER = QImage("./data/images/water.png")
	IMG_NPC = QImage("./data/images/npc.png")
	IMG_LEDGE_DOWN = QImage("./data/images/ledgedown.png")
	IMG_LEDGE_RIGHT = QImage("./data/images/ledgeright.png")
	IMG_LEDGE_LEFT = QImage("./data/images/ledgeleft.png")
	IMG_EXIT = QImage("./data/images/exit.png")
	IMG_OUTSIDE_BLOCK = QImage("./data/images/outsideblock.png")

	IMG_ROCK_RED = QImage("./data/images/rocks/red.png")
	IMG_ROCK_BLUE = QImage("./data/images/rocks/blue.png")
	IMG_ROCK_GREEN = QImage("./data/images/rocks/green.png")
	IMG_ROCK_PALE = QImage("./data/images/rocks/pale.png")
	IMG_ROCK_PRISM = QImage("./data/images/rocks/prism.png")
	IMG_ROCK_DARK = QImage("./data/images/rocks/dark.png")
	IMG_ROCK_RAINBOW = QImage("./data/images/rocks/rainbow.png")
	IMG_ROCK_EMPTY = QImage("./data/images/rocks/empty.png")


