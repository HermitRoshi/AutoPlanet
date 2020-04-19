import sys
import math

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from utils.constants import CONSTANTS
from ui.pokemonIconWidget import PokemonIconWidget
from ui.pokemonDetailsWidget import PokemonDetailsWidget
from pokemon import Pokemon

class PokemonWidget(QWidget):
	def __init__(self, parent):
		super(PokemonWidget, self).__init__(parent)
		
		self.setAttribute(Qt.WA_DeleteOnClose)

		self.__pokemon = None

		self.__barsWidget = QWidget()
		self.__mainLayout = QFormLayout()
		self.__mainLayout.setMargin(0)

		self.__barsLayout = QFormLayout()
		self.__barsLayout.setMargin(2)

		self.__image = PokemonIconWidget(0)
		self.__health = QProgressBar()
		self.__health.setAlignment(Qt.AlignCenter);
		self.__experience = QProgressBar()
		self.__experience.setAlignment(Qt.AlignCenter)
		self.__experience.setStyleSheet("QProgressBar::chunk {background: #ffa372;}")


		self.__barsLayout.addRow(self.__health)
		self.__barsLayout.addRow(self.__experience)
		self.__barsWidget.setLayout(self.__barsLayout)

		self.__mainLayout.addRow(self.__image, self.__barsWidget)

		self.setStyleSheet("QProgressBar {height: 10px;}")

		self.setLayout(self.__mainLayout)

	def mousePressEvent(self, ev):
		""" Handlesl the mouse press event for this widget"""

		# If its a left click and this widget has a pokemon, show details
		if ev.button() == Qt.MouseButton.LeftButton:
			if self.__pokemon is not None:
				self.showDetails()

	def reset(self):
		""" Reset this widget

			Clears the current pokemon and resets icon, health, and exp
		"""
		self.__pokemon = None
		self.__image.setIcon(0, "Empty")
		self.__health.setValue(0)
		self.__experience.setValue(0)


	def setPokemon(self, pokemon):
		self.__pokemon = pokemon
		self.__image.setIcon(pokemon.id, pokemon.name)
		self.__health.setMaximum(pokemon.health)
		self.__health.setValue(pokemon.currentHealth)
		self.__experience.setMaximum(pokemon.expForNextLevel())
		self.__experience.setValue(pokemon.levelExperience)
		self.update()

	def showDetails(self):
		details = PokemonDetailsWidget(self.__pokemon, self)
		details.exec_()