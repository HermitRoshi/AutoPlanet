from PySide2.QtCore import Signal, Qt
from PySide2.QtWidgets import (QWidget, 
							   QHBoxLayout,
							   QFormLayout, 
							   QLabel, 
							   QScrollArea, 
							   QPushButton, 
							   QListWidget, 
							   QComboBox)

from ui.catchRulesWidget import CatchRulesWidget
from utils.catchRule import CatchRule

import tomlkit
import os
import glob

class CatchConfigWidget(QWidget):
	saveChanges = Signal(object)
	def __init__(self, pokemonList, configDict, parent=None):
		super(CatchConfigWidget, self).__init__(parent)

		self.setAttribute(Qt.WA_DeleteOnClose)
		
		self.setWindowTitle("Catch Config")
		self.__ruleDict = dict()
		self.__currentConfigDict = configDict
		self.__pokeRuleMatchWidget = dict()

		self.__mainLayout = QHBoxLayout()

		self.__leftWidget = QWidget()
		self.__leftLayout = QFormLayout()
		self.__rulesLayout = QFormLayout()
		self.__rulesLayout.setSpacing(1)
		self.__rulesLayout.setMargin(2)
		self.__rulesWidget = QWidget()
		self.__rulesWidget.setLayout(self.__rulesLayout)

		pokemonLabel = QLabel("<b>Shiny</b>")
		self.__pokeRuleMatchWidget["Shiny"] = QComboBox()
		self.__rulesLayout.addRow(pokemonLabel, self.__pokeRuleMatchWidget["Shiny"])

		for pokemon in pokemonList:
			pokemonLabel = QLabel("<b>" + pokemon + "</b>")
			self.__pokeRuleMatchWidget[pokemon] = QComboBox()
			self.__rulesLayout.addRow(pokemonLabel, self.__pokeRuleMatchWidget[pokemon])

		self.__rulesScrollArea = QScrollArea()
		self.__rulesScrollArea.setMinimumSize(250, 250)
		self.__rulesScrollArea.setWidget(self.__rulesWidget)
		self.__rulesScrollArea.setWidgetResizable(True)

		self.__saveButton = QPushButton("Save")
		self.__saveButton.clicked.connect(self.__saveClicked)

		self.__leftLayout.addRow(self.__rulesScrollArea)
		self.__leftLayout.addRow(self.__saveButton)
		self.__leftWidget.setLayout(self.__leftLayout)

		self.__ruleManageWidget = QWidget()
		self.__ruleManageLayout = QHBoxLayout()
		self.__ruleManageLayout.setMargin(0)
		self.__ruleManageWidget.setLayout(self.__ruleManageLayout)

		self.__rightWidget = QWidget()
		self.__rightLayout = QFormLayout()
		self.__ruleListWidget = QListWidget()
		self.__newRuleButton = QPushButton("New Rule")
		self.__newRuleButton.clicked.connect(self.__newRuleClicked)
		self.__editRuleButton = QPushButton("Edit Rule")
		self.__editRuleButton.clicked.connect(self.__editRuleClicked)
		self.__deleteRuleButton = QPushButton("Delete Rule")
		self.__deleteRuleButton.clicked.connect(self.__deleteRuleClicked)
		self.__applyToAllButton = QPushButton("Apply To All")
		self.__applyToAllButton.clicked.connect(self.__applyToAllClicked)
		self.__ruleManageLayout.addWidget(self.__editRuleButton)
		self.__ruleManageLayout.addWidget(self.__deleteRuleButton)
		self.__ruleManageLayout.addWidget(self.__applyToAllButton)
		self.__rightLayout.addRow(self.__ruleListWidget)
		self.__rightLayout.addRow(self.__newRuleButton)
		self.__rightLayout.addRow(self.__ruleManageWidget)
		self.__rightWidget.setLayout(self.__rightLayout)

		self.__mainLayout.addWidget(self.__leftWidget)
		self.__mainLayout.addWidget(self.__rightWidget)
		self.setLayout(self.__mainLayout)

		self.__ruleConfigWidget = None

		self.__update()

	def __update(self):
		self.__loadRuleConfigs()
		self.__ruleListWidget.clear()

		ruleList = []
		for item in self.__ruleDict:
			self.__ruleListWidget.addItem(item)
			ruleList.append(item)

		for item in self.__pokeRuleMatchWidget:
			self.__pokeRuleMatchWidget[item].clear()
			self.__pokeRuleMatchWidget[item].addItems(ruleList)
			if len(self.__currentConfigDict) != 0 and item in self.__currentConfigDict:
				if self.__currentConfigDict[item].name in ruleList:
					self.__pokeRuleMatchWidget[item].setCurrentIndex(ruleList.index(self.__currentConfigDict[item].name))

	def __loadRuleConfigs(self):
		self.__ruleDict = dict()
		path = './config/catch_rules'
		for filename in glob.glob(os.path.join(path, '*.toml')):
			file = open(filename, "r")
			tomlDict = tomlkit.parse(file.read())

			self.__ruleDict[tomlDict["rule"]["name"]] = CatchRule(tomlDict["rule"]["name"],
																  tomlDict["rule"]["stop"],
																  tomlDict["rule"].get("sync", False),
																  tomlDict["rule"]["pokemon"],
																  tomlDict["rule"]["move"],
																  tomlDict["rule"]["status"],
																  tomlDict["rule"]["health"],
																  tomlDict["rule"]["pokeball"])

	def __newRuleClicked(self):
		self.__ruleConfigWidget = CatchRulesWidget()
		self.__ruleConfigWidget.saveChanges.connect(self.__update)
		self.__ruleConfigWidget.show()

	def __deleteRuleClicked(self):
		if self.__ruleListWidget.currentItem() is not None:
			selected_rule = "./config/catch_rules/" + self.__ruleListWidget.currentItem().text().replace(" ", "_") + ".toml"
			os.remove(selected_rule)
			self.__update()

	def __editRuleClicked(self):
		if self.__ruleListWidget.currentItem() is not None:
			self.__ruleConfigWidget = CatchRulesWidget(self.__ruleDict[self.__ruleListWidget.currentItem().text()])
			self.__ruleConfigWidget.saveChanges.connect(self.__update)
			self.__ruleConfigWidget.show()

	def __applyToAllClicked(self):
		if self.__ruleListWidget.currentItem() is not None:
			for pokemon in self.__pokeRuleMatchWidget:
				rule_name = self.__ruleListWidget.currentItem().text()
				rule_index = self.__pokeRuleMatchWidget[pokemon].findText(rule_name)
				self.__pokeRuleMatchWidget[pokemon].setCurrentIndex(rule_index)

	def __saveClicked(self):
		if len(self.__ruleDict) == 0:
			choice = QMessageBox.question(self, 'No Rule Defined!', "No rules defined, continue without catching pokemon?", QMessageBox.Yes | QMessageBox.No)

			if choice == QMessageBox.Yes:
				self.saveChanges.emit(dict())
				self.close()
		else:
			catch_dict = dict()
			for pokemon in self.__pokeRuleMatchWidget:
				catch_dict[pokemon] = self.__ruleDict[self.__pokeRuleMatchWidget[pokemon].currentText()]

			self.saveChanges.emit(catch_dict)
			self.close()
