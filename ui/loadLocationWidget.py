from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import (QWidget,
							   QDialog,
							   QFormLayout,
							   QLineEdit, 
							   QPushButton,
							   QListWidget)

import os
import tomlkit

class LoadLocationWidget(QDialog):
	loadLocationSignal = Signal(str, int, int)
	def __init__(self, parent=None):
		super(LoadLocationWidget, self).__init__(parent)

		self.setAttribute(Qt.WA_DeleteOnClose)
		
		self.setWindowTitle("Load Location")

		file = open("./config/favorite_locations.toml", "r")
		self.settingsDict = tomlkit.parse(file.read())
		self.__locationDict = dict()

		self.__mainLayout = QFormLayout()
		self.__locationList = QListWidget()
		
		for item in self.settingsDict["locations"]:
			data = self.settingsDict["locations"][item]
			key_string = "{} - [{}]".format(item, data[0])
			self.__locationDict[key_string] = item
			self.__locationList.addItem(key_string)

		self.__loadButton = QPushButton("Load")
		self.__loadButton.clicked.connect(self.__loadLocation)
		self.__deleteButton = QPushButton("Delete")
		self.__deleteButton.clicked.connect(self.__deleteLocation)

		self.__mainLayout.addRow(self.__locationList)
		self.__mainLayout.addRow(self.__loadButton, self.__deleteButton)

		self.setLayout(self.__mainLayout)

	def __loadLocation(self):
		location = self.settingsDict["locations"][self.__locationDict[self.__locationList.currentItem().text()]]
		self.loadLocationSignal.emit(str(location[0]), int(location[1]), int(location[2]))

	def __deleteLocation(self):
		item = self.__locationList.takeItem(self.__locationList.currentRow())
		if item is not None:
			del self.settingsDict["locations"][self.__locationDict[item.text()]]
			file = open("./config/favorite_locations.toml", "w")
			file.write(tomlkit.dumps(self.settingsDict))
			file.close()
