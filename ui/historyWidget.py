import sys

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

class HistoryWidget(QDockWidget):
	def __init__(self, parent):
		super(HistoryWidget, self).__init__(parent)

		self.setWindowTitle("Session History")

		self.__contentWidget = QWidget()
		self.__historyLayout = QFormLayout()
		self.__historyLayout.setMargin(1)

		self.battlesLabel = QPushButton("Battles: ", objectName='historyWidget')
		self.battlesLabel.setEnabled(False)
		self.battlesField = QLineEdit(objectName='historyWidget')
		self.battlesField.setAlignment(Qt.AlignRight)
		self.battlesField.setReadOnly(True)
		self.battlesField.setText("0")
		self.__historyLayout.addRow(self.battlesLabel, self.battlesField)

		self.moneyLabel = QPushButton("Money: ", objectName='historyWidget')
		self.moneyLabel.setEnabled(False)
		self.moneyField = QLineEdit(objectName='historyWidget')
		self.moneyField.setAlignment(Qt.AlignRight)
		self.moneyField.setReadOnly(True)
		self.moneyField.setText("0")
		self.__historyLayout.addRow(self.moneyLabel, self.moneyField)

		self.historyPokemonList = QListWidget()
		self.__historyLayout.addRow(self.historyPokemonList)

		self.__contentWidget.setLayout(self.__historyLayout)
		self.setWidget(self.__contentWidget)

		self.setStyleSheet("QPushButton:disabled#historyWidget {background-color: #6a8caf; color: #FFFFFF; font-weight: bold;}" +
		   		   		   "QLineEdit#historyWidget {background-color: #d1cebd; color: #424874; font-weight: bold; height: 20px;}")


	def update(self, battles, money, pokemon):
		""" Update session history.

			Sets new number of battles, money earned, pokemon encountered.
		"""
		self.battlesField.setText(str(battles))
		self.moneyField.setText(str(money))

		self.historyPokemonList.clear()

		for key, value in pokemon.items():
			label = key + ": " + str(value)
			self.historyPokemonList.addItem(label)

		self.historyPokemonList.sortItems()