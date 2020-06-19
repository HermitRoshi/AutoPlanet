import sys

from PySide2.QtWidgets import QWidget, QDockWidget, QFormLayout
from PySide2.QtCore import Signal

from ui.pokemonWidget import PokemonWidget
from pokemon import Pokemon
from utils.constants import CONSTANTS

class TeamWidget(QDockWidget):
	reorderSignal = Signal(int, int)
	removeItemSignal = Signal(int)
	def __init__(self, parent):
		super(TeamWidget, self).__init__(parent)

		self.setWindowTitle("Team")

		self.__contentWidget = QWidget()
		self.__teamLayout = QFormLayout()
		self.__teamLayout.setMargin(2)
		self.__team = []
		self.__teamSize = 0

		for pokemon in range(CONSTANTS.GAME_MAX_TEAM_SIZE):
			pokemonWidget = PokemonWidget(pokemon, self)
			pokemonWidget.reorderSignal.connect(self.__handleReorderSignal)
			pokemonWidget.removeItemSignal.connect(self.removeItemSignal.emit)
			self.__team.append(pokemonWidget)
			self.__teamLayout.addRow(pokemonWidget)

		self.__contentWidget.setLayout(self.__teamLayout)
		self.setWidget(self.__contentWidget)

		self.setFeatures(QDockWidget.DockWidgetMovable)
		self.__contentWidget.setFixedWidth(200)
		self.__contentWidget.setMaximumSize(200,274)

	def setTeam(self, team):
		if len(team) != self.__teamSize:
			self.__teamSize = len(team)
			for member in self.__team:
				member.reset()
			
		for pokemon in range(len(team)):
			self.__team[pokemon].setPokemon(team[pokemon])

	def __handleReorderSignal(self, move_from, move_to):
		self.reorderSignal.emit(move_from, move_to)