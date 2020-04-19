from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

import csv

class ListSelectionWidget(QWidget):
	listChanges = Signal(object)
	def __init__(self, secondaryList, secondaryListLabel, title, parent=None):
		super(ListSelectionWidget, self).__init__(parent)

		self.setAttribute(Qt.WA_DeleteOnClose)
		
		self.setWindowTitle(title)
		self.__layout = QHBoxLayout()

		self.__leftWidget = QWidget()
		self.__centerWidget = QWidget()
		self.__rightWidget = QWidget()
		self.__leftLayout = QVBoxLayout()
		self.__centerLayout = QVBoxLayout()
		self.__rightLayout = QVBoxLayout()

		self.__primaryLabel = QLabel("<b>All Pokemon</b>")
		self.__primaryList = QListWidget()
		self.__secondaryLabel = QLabel("<b>" + secondaryListLabel + "</b>")
		self.__secondaryList = QListWidget()
		self.__resetButton = QPushButton("Reset")
		self.__saveButton = QPushButton("Save")

		self.__leftLayout.addWidget(self.__primaryLabel)
		self.__leftLayout.addWidget(self.__primaryList)
		self.__leftWidget.setLayout(self.__leftLayout)

		self.__centerLayout.addWidget(self.__resetButton)
		self.__centerLayout.addWidget(self.__saveButton)
		self.__centerWidget.setLayout(self.__centerLayout)

		self.__rightLayout.addWidget(self.__secondaryLabel)
		self.__rightLayout.addWidget(self.__secondaryList)
		self.__rightWidget.setLayout(self.__rightLayout)

		# Load up pokemon csv here. To make this class more generic one
		# can pass in a file path instead.
		file = open('csv\\pokemon.csv')
		self.__pokemonList = list(csv.DictReader(file, delimiter=','))

		# Fill up primary list. Make sure not to have double in secondary
		for pokemon in self.__pokemonList:
			name = pokemon['identifier'].replace("-", " ").title()
			if name not in secondaryList:
				self.__primaryList.addItem(name)

		# Fill up secondary list from passed in variable
		for name in secondaryList:
			self.__secondaryList.addItem(name)

		# Alphabetical is better to read
		self.__sortLists()

		self.__layout.addWidget(self.__leftWidget)
		self.__layout.addWidget(self.__centerWidget)
		self.__layout.addWidget(self.__rightWidget)
		self.setLayout(self.__layout)

		# Connect signals
		self.__resetButton.clicked.connect(self.__resetLists)
		self.__saveButton.clicked.connect(self.__saveChanges)
		self.__primaryList.itemDoubleClicked.connect(self.__primaryDoubleClick)
		self.__secondaryList.itemDoubleClicked.connect(self.__secondaryDoubleClick)

	def __sortLists(self):
		self.__primaryList.sortItems()
		self.__secondaryList.sortItems()

	def __primaryDoubleClick(self, item):
		self.__primaryList.takeItem(self.__primaryList.row(item))
		self.__secondaryList.addItem(item.text())
		self.__sortLists()

	def __secondaryDoubleClick(self, item):
		self.__secondaryList.takeItem(self.__secondaryList.row(item))
		self.__primaryList.addItem(item.text())
		self.__sortLists()

	def __resetLists(self):
		self.__primaryList.clear()
		self.__secondaryList.clear()
		for pokemon in self.__pokemonList:
			name = pokemon['identifier'].replace("-", " ").title()
			self.__primaryList.addItem(name)
		self.__sortLists()

	def __saveChanges(self):
		pokemonList = []
		for pokemon in range(self.__secondaryList.count()):
			item = self.__secondaryList.item(pokemon)
			pokemonList.append(item.text())

		self.listChanges.emit(pokemonList)
		self.close()