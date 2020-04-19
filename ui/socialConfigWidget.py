from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

import tomlkit
import os
import glob

class SocialConfigWidget(QWidget):
	saveChanges = Signal(object)
	def __init__(self, pokemonList, parent=None):
		super(SocialConfigWidget, self).__init__(parent)

		self.setAttribute(Qt.WA_DeleteOnClose)
		
		self.setWindowTitle("Social Config")

		self.__avoidPlayers = []
		self.__chatResponses = [[]]

		self.__mainLayout = QHBoxLayout()

		self.__playerAvoidLabel = QLabel("<b>Avoid Players</b>")
		self.__leftLayout = QFormLayout()
		self.__leftWidget = QWidget()
		self.__leftWidget.setLayout(self.__leftLayout)

		self.__chatResponseLabel = QLabel("<b>Private Message Response</b>")
		self.__rightLayout = QFormLayout()
		self.__rightWidget = QWidget()
		self.__rightWidget.setLayout(self.__rightLayout)

		self.__playerList = QListWidget()
		self.__addPlayerButton = QPushButton("Add Player")
		self.__removePlayerButton = QPushButton("Remove Player")

		self.__addChatRuleButton = QPushButton("Add Chat Rule")
		self.__removeChatRuleButton = QPushButton("Remove Chat Rule")

		self.__resetButton = QPushButton("Reset")
		self.__saveButton = QPushButton("Save")

		self.__leftLayout.addRow(self.__playerAvoidLabel)
		self.__leftLayout.addRow(self.__playerList)
		self.__leftLayout.addRow(self.__addPlayerButton)
		self.__leftLayout.addRow(self.__removePlayerButton)

		self.__mainLayout.addWidget(self.__leftWidget)
		self.__mainLayout.addWidget(self.__rightWidget)
		self.setLayout(self.__mainLayout)

		self.__update()