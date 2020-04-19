import sys

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from ui.pokemonWidget import PokemonWidget
from pokemon import Pokemon
from utils.constants import CONSTANTS

class TeamWidget(QDockWidget):
	def __init__(self, parent):
		super(TeamWidget, self).__init__(parent)

		self.setWindowTitle("Team")

		self.__contentWidget = QWidget()
		self.__teamLayout = QFormLayout()
		self.__teamLayout.setMargin(2)
		self.__team = []
		self.__teamSize = 0

		for pokemon in range(CONSTANTS.GAME_MAX_TEAM_SIZE):
			pokemonWidget = PokemonWidget(self)
			self.__team.append(pokemonWidget)
			self.__teamLayout.addRow(pokemonWidget)

		self.__contentWidget.setLayout(self.__teamLayout)
		self.setWidget(self.__contentWidget)

		self.setFeatures(QDockWidget.DockWidgetMovable)
		self.__contentWidget.setMaximumSize(200,274)

	def setTeam(self, team):
		if len(team) != self.__teamSize:
			self.__teamSize = len(team)
			for member in self.__team:
				member.reset()
			
		for pokemon in range(len(team)):
			self.__team[pokemon].setPokemon(team[pokemon])