from PySide2.QtCore import Signal, Qt, QModelIndex
from PySide2.QtWidgets import (QWidget,
							   QDialog,
							   QVBoxLayout,
							   QHBoxLayout,
							   QLabel,
							   QLineEdit,
							   QComboBox,
							   QPushButton,
							   QTableWidget,
							   QTableWidgetItem,
							   QAbstractScrollArea)

import os
from functools import partial
from pokemon import Pokemon
from ui.qCustomTableWidgetItem import QCustomTableWidgetItem
from ui.pokemonDetailsWidget import PokemonDetailsWidget

class GlobalMarketplaceWidget(QDialog):
	searchSignal = Signal(str, str)
	buySignal = Signal(str)
	def __init__(self, parent=None):
		super(GlobalMarketplaceWidget, self).__init__(parent)

		self.setAttribute(Qt.WA_DeleteOnClose)
		
		self.setWindowTitle("Global Marketplace")
		self.setMinimumHeight(350)

		self.__mainLayout = QVBoxLayout()

		self.__searchLayout = QHBoxLayout()
		self.__searchWidget = QWidget()
		self.__searchWidget.setLayout(self.__searchLayout)
		self.__searchBox = QLineEdit()
		self.__searchType = QComboBox()
		self.__searchType.addItems(["all", "pokemon", "consumables"])
		self.__searchButton = QPushButton("Search")
		self.__searchButton.clicked.connect(self.__search)
		self.__searchLayout.addWidget(self.__searchBox)
		self.__searchLayout.addWidget(self.__searchType)
		self.__searchLayout.addWidget(self.__searchButton)

		self.__itemTable = QTableWidget()
		self.__itemTable.setColumnCount(13)
		self.__itemTable.setSortingEnabled(True)
		self.__itemTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
		self.__itemTable.setHorizontalHeaderLabels(["Name", "Count", "Price", "Ability", "Nature", "Hp", "Atk", "Def", "Spec.Atk", "Spec.Def", "Speed", "$ Per Item", "Buy"])
		self.__itemTable.resizeColumnsToContents()

		self.__mainLayout.addWidget(self.__searchWidget)
		self.__mainLayout.addWidget(self.__itemTable)

		self.setLayout(self.__mainLayout)

	def __search(self):
		self.__searchButton.setText("Searching...")
		self.__searchButton.setEnabled(False)
		self.searchSignal.emit(self.__searchBox.text(), self.__searchType.currentText())

	def searchResults(self, data):
		# Reset table
		self.__searchButton.setText("Populating...")
		self.__searchButton.setEnabled(False)
		self.__itemTable.setSortingEnabled(False)
		self.__itemTable.setRowCount(0)

		for item_index in range(len(data)):
			item = data[item_index].split(",")
			# Make sure it at least has item data
			if len(item) >= 3:
				row_data = []
				# This is an item if it has no pokemon info
				if item[2] == "":
					row_data = ["0"] * self.__itemTable.columnCount()
					row_data[0] = item[1]
					row_data[1] = item[3]
					row_data[2] = "{:,}".format(int(item[4]))
					row_data[self.__itemTable.columnCount() - 2] = "{:,}".format(int(int(item[4]) / int(item[3])))

					self.__populateRow(row_data, item[9])
				elif len(item) == 50:
					construct = item[1:2]

					pokemon_data = []
					for field_num in range(2, 43):
						if field_num == 2:
							pokemon_data.append(item[field_num].replace("[", ""))
						elif field_num == 42:
							pokemon_data.append(item[field_num].replace("]]", "]"))
						else:
							pokemon_data.append(item[field_num])

					construct.append(pokemon_data)
					construct.append(item[43])
					construct.append(item[44])
					construct.append(item[49].replace("]", ""))

					item = construct
					row_data.append(item[0])
					row_data.append(item[2])
					row_data.append("{:,}".format(int(item[3])))

					pokemon = Pokemon(",".join(item[1]))
					row_data.append(pokemon.ability.name)
					row_data.append(pokemon.nature)
					row_data.append(pokemon.healthIV)
					row_data.append(pokemon.attackIV)
					row_data.append(pokemon.defenseIV)
					row_data.append(pokemon.specAtkIV)
					row_data.append(pokemon.specDefIV)
					row_data.append(pokemon.speedIV)
					row_data.append("{:,}".format(int(int(item[3]) / int(item[2]))))
					self.__populateRow(row_data, item[4], pokemon)


		self.__itemTable.resizeColumnsToContents()
		self.__searchButton.setText("Search")
		self.__searchButton.setEnabled(True)
		self.__itemTable.setSortingEnabled(True)

	def __populateRow(self, row_data, item_id, pokemon_data=None):
		row_position = self.__itemTable.rowCount()
		self.__itemTable.insertRow(row_position)

		for col_index in range(len(row_data)):
			# For columns with string data use original TableWidgetItem, otherwise use cutom for sorting.
			if col_index != 0 and col_index != 3 and col_index != 4:
				self.__itemTable.setItem(row_position, col_index, QCustomTableWidgetItem(str(row_data[col_index])))
			elif col_index == 0 and pokemon_data is not None:
				pokemon_button = QPushButton(str(row_data[col_index]))
				pokemon_button.clicked.connect(partial(self.__pokemonClicked, pokemon_data))
				self.__itemTable.setCellWidget(row_position, col_index, pokemon_button)
			else:
				self.__itemTable.setItem(row_position, col_index, QTableWidgetItem(str(row_data[col_index])))

		# Add the buy button
		buy_button = QPushButton("Buy")
		buy_button.clicked.connect(partial(self.__buyItem, item_id))
		self.__itemTable.setCellWidget(row_position, 12, buy_button)

	def __buyItem(self, item_id):
		self.buySignal.emit(item_id)

	def __pokemonClicked(self, pokemon_data):
		details = PokemonDetailsWidget(pokemon_data, -1, self)
		details.exec_()