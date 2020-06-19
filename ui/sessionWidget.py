import sys

from PySide2.QtWidgets import (QDockWidget, 
							   QWidget, 
							   QFormLayout, 
							   QPushButton, 
							   QLineEdit, 
							   QListWidget,
							   QTabWidget,
							   QListWidgetItem)
from PySide2.QtGui import Qt, QColor

class SessionWidget(QDockWidget):
	def __init__(self, parent):
		super(SessionWidget, self).__init__(parent)

		self.setWindowTitle("Session Info")
		self.setFeatures(QDockWidget.DockWidgetMovable)
		
		self.__contentWidget = QWidget()
		self.__historyLayout = QFormLayout()
		self.__historyLayout.setMargin(1)
		self.__historyTabs = QTabWidget()

		self.battlesLabel = QPushButton("Battles: ", objectName='sessionWidget')
		self.battlesLabel.setEnabled(False)
		self.battlesField = QLineEdit(objectName='sessionWidget')
		self.battlesField.setAlignment(Qt.AlignRight)
		self.battlesField.setReadOnly(True)
		self.battlesField.setText("0")
		self.__historyLayout.addRow(self.battlesLabel, self.battlesField)

		self.moneyLabel = QPushButton("Money: ", objectName='sessionWidget')
		self.moneyLabel.setEnabled(False)
		self.moneyField = QLineEdit(objectName='sessionWidget')
		self.moneyField.setAlignment(Qt.AlignRight)
		self.moneyField.setReadOnly(True)
		self.moneyField.setText("0")
		self.__historyLayout.addRow(self.moneyLabel, self.moneyField)

		self.historyPokemonList = QListWidget()
		self.historyItemList = QListWidget()
		self.playerList = QListWidget()
		self.__historyTabs.addTab(self.historyPokemonList, "Pokemon")
		self.__historyTabs.addTab(self.historyItemList, "Items")
		self.__historyTabs.addTab(self.playerList, "Players")
		self.__historyLayout.addRow(self.__historyTabs)

		self.__contentWidget.setLayout(self.__historyLayout)
		self.setWidget(self.__contentWidget)

		self.setStyleSheet("QPushButton:disabled#sessionWidget {background-color: #0a64a0; color: #FFFFFF; font-weight: bold;}" +
		   		   		   "QLineEdit#sessionWidget {background-color: #d1cebd; color: #424874; font-weight: bold;}")


	def update(self, battles, money, pokemon, items):
		""" Update session history.

			Sets new number of battles, money earned, pokemon encountered.
		"""
		self.battlesField.setText(str(battles))
		self.moneyField.setText(str(money))

		self.historyPokemonList.clear()
		self.historyItemList.clear()

		for key, value in pokemon.items():
			label = key + ": " + str(value)
			self.historyPokemonList.addItem(label)

		for key, value in items.items():
			label = key + ": " + str(value)
			self.historyItemList.addItem(label)

		self.historyPokemonList.sortItems()
		self.historyItemList.sortItems()

	def updatePlayers(self, playersDict):
		self.playerList.clear()
		for player in playersDict:
			color = "#FFFFFF"

			if playersDict[player][1] == "0":
				color = "#FF3737"
			elif playersDict[player][1] == "1":
				color = "#00FFFF"
			elif playersDict[player][1] == "2":
				color = "#00FF00"
			elif playersDict[player][1] == "3":
				color = "#00FF00"
			elif playersDict[player][1] == "4":
				color = "#F5A402"
			elif playersDict[player][1] == "5":
				color = "#00FF00"
			elif playersDict[player][1] == "6":
				color = "#FF9900"
			elif playersDict[player][1] == "7":
				color = "#9B59B6"

			item = QListWidgetItem(playersDict[player][0], self.playerList)
			item.setTextColor(QColor(color))
			self.playerList.addItem(item)

		self.playerList.sortItems()
		self.__historyTabs.setTabText(2, "Players[{}]".format(len(playersDict)))