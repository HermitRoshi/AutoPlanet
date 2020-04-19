from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

import tomlkit
import os

class CatchRulesWidget(QWidget):
	saveChanges = Signal()
	def __init__(self, rule=None, parent=None):
		super(CatchRulesWidget, self).__init__(parent)

		self.setAttribute(Qt.WA_DeleteOnClose)
		self.setWindowTitle("Rule")
		
		self.__layout = QFormLayout()
		self.__nameLabel = QLabel("Rule Name:")
		self.__pokemonLabel = QLabel("Pokemon:")
		self.__moveLabel = QLabel("Move:")
		self.__statusLabel = QLabel("Status:")
		self.__healthLabel = QLabel("Health(%):")
		self.__pokeballLabel = QLabel("Pokeball:")
		self.__confirmRuleButton = QPushButton("Save Changes")
		self.__confirmRuleButton.clicked.connect(self.__saveChangesClicked)

		self.__pokemonInput = QComboBox()
		self.__stopBotCheck = QCheckBox("Stop Bot")
		self.__moveInput = QComboBox()
		self.__statusInput = QComboBox()
		self.__healthInput = QLineEdit()
		self.__pokeballInput = QComboBox()

		self.__pokeballInput.addItems(["Any", "Pokeball", "Great Ball", "Ultra Ball", "Safari Ball"])
		self.__pokemonInput.addItems(["Slot 1", "Slot 2", "Slot 3", "Slot 4", "Slot 5", "Slot 6"])
		self.__statusInput.addItems(["None", "Paralysis", "Sleep", "Burn", "Freeze", "Poison"])
		self.__moveInput.addItems(["Slot 1", "Slot 2", "Slot 3", "Slot 4"])
		self.__stopBotCheck.stateChanged.connect(self.__stopBotCheckClicked)

		if rule is not None:
			self.__nameInput = QLineEdit(rule.name)
			self.__stopBotCheck.setChecked(rule.stop)
			self.__healthInput.setText(str(rule.health))
			self.__pokemonInput.setCurrentIndex(rule.pokemon)
			self.__moveInput.setCurrentIndex(rule.move)
			self.__statusInput.setCurrentIndex(self.__statusInput.findText(rule.status, Qt.MatchFixedString))
			self.__pokeballInput.setCurrentIndex(self.__pokeballInput.findText(rule.pokeball, Qt.MatchFixedString))
			self.__oldName = rule.name

		else:
			self.__oldName = None
			self.__nameInput = QLineEdit("New Rule")
			self.__healthInput.setText("50")




		self.__layout.addRow(self.__nameLabel, self.__nameInput)
		self.__layout.addRow(self.__stopBotCheck)
		self.__layout.addRow(self.__pokemonLabel, self.__pokemonInput)
		self.__layout.addRow(self.__moveLabel, self.__moveInput)
		self.__layout.addRow(self.__statusLabel, self.__statusInput)
		self.__layout.addRow(self.__healthLabel, self.__healthInput)
		self.__layout.addRow(self.__pokeballLabel, self.__pokeballInput)
		self.__layout.addRow(self.__confirmRuleButton)


		self.setLayout(self.__layout)

	def __stopBotCheckClicked(self):
		if self.__stopBotCheck.checkState():
			self.__pokemonInput.setEnabled(False)
			self.__moveInput.setEnabled(False)
			self.__statusInput.setEnabled(False)
			self.__healthInput.setEnabled(False)
			self.__pokeballInput.setEnabled(False)
		else:
			self.__pokemonInput.setEnabled(True)
			self.__moveInput.setEnabled(True)
			self.__statusInput.setEnabled(True)
			self.__healthInput.setEnabled(True)
			self.__pokeballInput.setEnabled(True)

	def __saveChangesClicked(self):
		filename = "./config/catch_rules/" + self.__nameInput.text().replace(" ", "_") + ".toml"
		file = open(filename, "w")

		tomlDict = dict()

		tomlDict["rule"] = dict()
		tomlDict["rule"]["name"] = self.__nameInput.text()
		tomlDict["rule"]["stop"] = self.__stopBotCheck.isChecked()
		tomlDict["rule"]["pokemon"] = int(self.__pokemonInput.currentText().split("Slot ")[1]) - 1
		tomlDict["rule"]["move"] = int(self.__moveInput.currentText().split("Slot ")[1]) - 1
		tomlDict["rule"]["status"] = self.__statusInput.currentText()
		tomlDict["rule"]["health"] = int(self.__healthInput.text())
		tomlDict["rule"]["pokeball"] = self.__pokeballInput.currentText()

		file.write(tomlkit.dumps(tomlDict))
		file.close()

		if self.__oldName is not None and (self.__oldName != self.__nameInput.text()):
			old_rule_name = "./config/catch_rules/" + self.__oldName.replace(" ", "_") + ".toml"
			os.remove(old_rule_name)

		self.saveChanges.emit()
		self.close()