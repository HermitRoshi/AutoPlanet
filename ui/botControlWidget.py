import sys
import os
import tomlkit

from PySide2.QtCore import Signal, Qt
from PySide2.QtWidgets import (QWidget, 
							   QDockWidget,
							   QFormLayout,
							   QHBoxLayout,
							   QPushButton,
							   QLabel,
							   QListWidget,
							   QSlider,
							   QComboBox,
							   QMessageBox,
							   QGridLayout)

from playerInfo import PlayerInfo
from botRules import BotRules
from utils.advanceRules import AdvanceRules

from ui.horizontalLineWidget import HorizontalLineWidget
from ui.listSelectionWidget import ListSelectionWidget
from ui.catchConfigWidget import CatchConfigWidget
from ui.advanceSettingsWidget import AdvanceSettingsWidget

class BotControlWidget(QDockWidget):
	modeSignal = Signal(str)
	startSignal = Signal(bool, object)

	def __init__(self, parent):
		super(BotControlWidget, self).__init__(parent)

		self.setWindowTitle("Bot Control")
		self.setFeatures(QDockWidget.DockWidgetMovable)

		self.__contentWidget = QWidget()
		self.__contentWidget.setFixedWidth(220)

		self.__controlLayout = QFormLayout()
		self.__controlLayout.setFormAlignment(Qt.AlignHCenter)
		self.__controlLayout.setMargin(2)
		self.__controlLayout.setSpacing(1)

		self.__mouseModeWidget = QWidget()
		self.__mouseModeLayout = QHBoxLayout()
		self.__mouseModeLayout.setMargin(2)
		self.__mouseModeLayout.setSpacing(1)
		self.__mouseModeWidget.setLayout(self.__mouseModeLayout)

		self.__mouseSelectButton = QPushButton("Select Mode")
		self.__mouseSelectButton.setEnabled(False)
		self.__mouseSelectButton.clicked.connect(self.__selectModeClicked)
		self.__mouseWalkButton = QPushButton("Walk Mode")
		self.__mouseWalkButton.clicked.connect(self.__walkModeClicked)

		self.__mouseModeLayout.addWidget(self.__mouseSelectButton)
		self.__mouseModeLayout.addWidget(self.__mouseWalkButton)

		self.__controlLayout.addRow(self.__mouseModeWidget)

		line = HorizontalLineWidget(5)
		self.__controlLayout.addRow(line)

		self.__botModeLabel = QLabel("Bot Mode: ")
		self.__botMode = QComboBox()
		self.__botMode.addItems(["Battle", "Fish", "Mine"])
		self.__controlLayout.addRow(self.__botModeLabel, self.__botMode)

		self.__learnMoveLabel = QLabel("New Moves: ")
		self.__learnMove = QComboBox()
		self.__learnMove.addItems(["Don't Learn", "Replace 1", "Replace 2", "Replace 3", "Replace 4",])
		self.__controlLayout.addRow(self.__learnMoveLabel, self.__learnMove)

		self.__evolveLabel = QLabel("Evolve: ")
		self.__evolveBox = QComboBox()
		self.__evolveBox.addItems(["No", "Yes"])
		self.__controlLayout.addRow(self.__evolveLabel, self.__evolveBox)

		self.__eliteLabel = QLabel("Avoid Elite: ")
		self.__eliteBox = QComboBox()
		self.__eliteBox.addItems(["No", "Yes"])
		self.__controlLayout.addRow(self.__eliteLabel, self.__eliteBox)

		self.__hHealWidget = QWidget()
		self.__hHealLayout = QHBoxLayout()
		self.__hHealLayout.setMargin(1)
		self.__hHealLayout.setSpacing(1)
		self.__hHealWidget.setLayout(self.__hHealLayout)
		self.__healLabel = QLabel("<b>Heal: 50%</b>")
		self.__healSlider = QSlider(Qt.Horizontal)
		self.__healSlider.valueChanged.connect(self.__healSliderChanged)
		self.__healSlider.setMinimum(0)
		self.__healSlider.setMaximum(99)
		self.__healSlider.setValue(50)
		self.__hHealLayout.addWidget(self.__healLabel, 30)
		self.__hHealLayout.addWidget(self.__healSlider, 70)

		self.__controlLayout.addRow(self.__hHealWidget)

		self.__hSpeedWidget = QWidget()
		self.__hSpeedLayout = QHBoxLayout()
		self.__hSpeedLayout.setMargin(1)
		self.__hSpeedLayout.setSpacing(1)
		self.__hSpeedWidget.setLayout(self.__hSpeedLayout)
		self.__speedLabel = QLabel("<b>Speed: 5</b>")
		self.__speedSlider = QSlider(Qt.Horizontal, objectName='speedSlider')
		self.__speedSlider.valueChanged.connect(self.__speedSliderChanged)
		self.__speedSlider.setMinimum(1)
		self.__speedSlider.setMaximum(6)
		self.__speedSlider.setValue(3)
		self.__hSpeedLayout.addWidget(self.__speedLabel, 30)
		self.__hSpeedLayout.addWidget(self.__speedSlider, 70)

		self.__controlLayout.addRow(self.__hSpeedWidget)

		self.__controlLayout.addRow(HorizontalLineWidget(5))

		self.__advanceSettingsButton = QPushButton("Advance Settings")
		self.__advanceSettingsButton.clicked.connect(self.__advanceSettingsClicked)
		self.__controlLayout.addRow(self.__advanceSettingsButton)

		self.__controlLayout.addRow(HorizontalLineWidget(5))

		self.__listsWidget = QWidget()
		self.__listsLayout = QGridLayout()
		self.__listsLayout.setMargin(1)
		self.__listsLayout.setSpacing(1)
		self.__listsWidget.setLayout(self.__listsLayout)

		self.__catchListButton = QPushButton("Change Catch List")
		self.__catchListButton.clicked.connect(self.__changeCatchClicked)
		self.__catchConfigButton = QPushButton("Config Catching")
		self.__catchConfigButton.setStyleSheet("background-color: #ffd3b5; color: #000000; font-weight: bold;")
		self.__catchConfigButton.clicked.connect(self.__catchConfigClicked)
		self.__catchList = QListWidget()

		self.__avoidListButton = QPushButton("Change Avoid List")
		self.__avoidListButton.clicked.connect(self.__changeVoidClicked)
		self.__avoidList = QListWidget()


		self.__listsLayout.addWidget(self.__catchListButton, 0, 0)
		self.__listsLayout.addWidget(self.__avoidListButton, 0, 1)
		self.__listsLayout.addWidget(self.__catchList, 1, 0)
		self.__listsLayout.addWidget(self.__avoidList, 1, 1)

		self.__controlLayout.addRow(self.__catchConfigButton)
		self.__controlLayout.addRow(self.__listsWidget)

		self.__startBot = QPushButton("Start")
		self.__startBot.clicked.connect(self.__startBotClicked)
		self.__controlLayout.addRow(self.__startBot)
		

		self.__contentWidget.setLayout(self.__controlLayout)
		self.setWidget(self.__contentWidget)
		self.setStyleSheet("QSlider::handle:horizontal {background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ccc); border: 1px solid #777; width: 13px; margin-top: -2px; margin-bottom: -2px; border-radius: 4px;}" +
						   "QSlider::groove:horizontal {border: 1px solid #bbb; background: white; height: 10px; border-radius: 4px;}" +
						   "QSlider::sub-page:horizontal { background: qlineargradient(x1: 0, y1: 0,    x2: 0, y2: 1, stop: 0 #9f0, stop: 1 #8c0); background: qlineargradient(x1: 0, y1: 0.2, x2: 1, y2: 1, stop: 0 #8c0, stop: 1 #9f0); border: 1px solid #777; height: 10px; border-radius: 4px; }" +
						   "QSlider::add-page:horizontal { background: #c53; border: 1px solid #777; height: 10px; border-radius: 4px; }" +
						   "QSlider::handle:horizontal#speedSlider {background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ccc); border: 1px solid #777; width: 13px; margin-top: -2px; margin-bottom: -2px; border-radius: 4px;}" +
						   "QSlider::groove:horizontal#speedSlider {border: 1px solid #bbb; background: white; height: 10px; border-radius: 4px;}" +
						   "QSlider::sub-page:horizontal#speedSlider { background: qlineargradient(x1: 0, y1: 0,    x2: 0, y2: 1, stop: 0 #46f, stop: 1 #4af); background: qlineargradient(x1: 0, y1: 0.2, x2: 1, y2: 1, stop: 0 #4af, stop: 1 #46f); border: 1px solid #777; height: 10px; border-radius: 4px; }" +
						   "QSlider::add-page:horizontal#speedSlider { background: #fd0; border: 1px solid #777; height: 10px; border-radius: 4px; }")

		self.__advanceSettingsWidget = None
		self.__needUpdateConfig = False
		self.__catchSelectionWidget = None
		self.__catchConfigWidget = None
		self.__catchConfigDict = dict()
		self.__avoidSelectionWidget = None

		self.__advanceRules = AdvanceRules()

		if os.path.exists("./config/session_settings.toml"):
			file = open("./config/session_settings.toml", "r")
			settings_dict = tomlkit.parse(file.read())

			# General Advance Settings
			self.__advanceRules.stopCatchLogout = settings_dict["stopCatchLogout"]
			self.__advanceRules.takeLogoutBreak = settings_dict["takeLogoutBreak"]
			self.__advanceRules.fastFish = settings_dict["fastFish"]
			self.__advanceRules.fastMine = settings_dict["fastMine"]
			# Social Advance Settings
			self.__advanceRules.tradePopup = settings_dict["tradePopup"]
			self.__advanceRules.tradeAudio = settings_dict["tradeAudio"]
			self.__advanceRules.battlePopup = settings_dict["battlePopup"]
			self.__advanceRules.battleAudio = settings_dict["battleAudio"]
			self.__advanceRules.clanPopup = settings_dict["clanPopup"]
			self.__advanceRules.clanAudio = settings_dict["clanAudio"]
			self.__advanceRules.pmPopup = settings_dict["pmPopup"]
			self.__advanceRules.pmAudio = settings_dict["pmAudio"]

			self.__catchList.addItems(settings_dict["catch"])
			self.__avoidList.addItems(settings_dict["avoid"])

			if len(settings_dict["catch"]) > 0:
				self.__catchConfigButton.setStyleSheet("background-color: #f67280; color: #000000; font-weight: bold;")
				self.__needUpdateConfig = True

	def __selectModeClicked(self):
		self.__mouseSelectButton.setEnabled(False)
		self.__mouseWalkButton.setEnabled(True)
		self.modeSignal.emit("select")

	def __walkModeClicked(self):
		self.__mouseSelectButton.setEnabled(True)
		self.__mouseWalkButton.setEnabled(False)
		self.modeSignal.emit("walk")

	def __healSliderChanged(self):
		value = ""
		if self.__healSlider.value() < 10:
			value = "0" + str(self.__healSlider.value())
		else:
			value = str(self.__healSlider.value())

		self.__healLabel.setText("<b>Heal: " + value + "%</b>" )

	def __speedSliderChanged(self):
		value = ""
		if self.__speedSlider.value() < 10:
			value = "0" + str(self.__speedSlider.value())
		else:
			value = str(self.__speedSlider.value())

		self.__speedLabel.setText("<b>Speed: " + value + "</b>" )

	def __catchConfigClicked(self):
		items = []
		for index in range(self.__catchList.count()):
			items.append(self.__catchList.item(index))
		pokemon = [i.text() for i in items]

		self.__catchConfigWidget = CatchConfigWidget(pokemon, self.__catchConfigDict)
		self.__catchConfigWidget.saveChanges.connect(self.__handleCatchConfig)
		self.__catchConfigWidget.show()

	def __advanceSettingsClicked(self):
		self.__advanceSettingsWidget = AdvanceSettingsWidget(self.__advanceRules)
		self.__advanceSettingsWidget.settingsSavedSignal.connect(self.__handleAdvanceSettings)
		self.__advanceSettingsWidget.show()

	def __handleCatchConfig(self, config):
		self.__catchConfigDict = config
		self.__needUpdateConfig = False
		self.__catchConfigButton.setStyleSheet("background-color: #7effdb; color: #000000; font-weight: bold;")
		self.update()

	def __startBotClicked(self):

		if self.__startBot.text() == "Start":
			if not self.__needUpdateConfig:
				answer = QMessageBox.Yes
				if len(self.__catchConfigDict) == 0:
					answer = QMessageBox.question(self, 'No Catch Config!', "No catch pokemon listed, proceed without catching?", QMessageBox.Yes, QMessageBox.No)

				if answer == QMessageBox.Yes:
					mode = self.__botMode.currentText()
					evolve = self.__evolveBox.currentText() == "Yes"
					avoidElite = self.__eliteBox.currentText() == "Yes"
					healThreshold = self.__healSlider.value()/100
					speed = self.__speedSlider.value()
					learnMove = 4

					if self.__learnMove.currentText() == "Replace 1":
						learnMove = 0
					elif self.__learnMove.currentText() == "Replace 2":
						learnMove = 1
					elif self.__learnMove.currentText() == "Replace 3":
						learnMove = 2
					elif self.__learnMove.currentText() == "Replace 4":
						learnMove = 3

					catchList = []
					for pokemon in range(self.__catchList.count()):
						item = self.__catchList.item(pokemon)
						catchList.append(item.text())

					avoidList = []
					for pokemon in range(self.__avoidList.count()):
						item = self.__avoidList.item(pokemon)
						avoidList.append(item.text())

					# Write current settings to file
					settings_dict = dict()
					# General Advance Settings
					settings_dict["stopCatchLogout"] = self.__advanceRules.stopCatchLogout
					settings_dict["takeLogoutBreak"] = self.__advanceRules.takeLogoutBreak
					settings_dict["fastFish"] = self.__advanceRules.fastFish
					settings_dict["fastMine"] = self.__advanceRules.fastMine
					# Social Advance Settings
					settings_dict["tradePopup"] = self.__advanceRules.tradePopup
					settings_dict["tradeAudio"] = self.__advanceRules.tradeAudio
					settings_dict["battlePopup"] = self.__advanceRules.battlePopup
					settings_dict["battleAudio"] = self.__advanceRules.battleAudio
					settings_dict["clanPopup"] = self.__advanceRules.clanPopup
					settings_dict["clanAudio"] = self.__advanceRules.clanAudio
					settings_dict["pmPopup"] = self.__advanceRules.pmPopup
					settings_dict["pmAudio"] = self.__advanceRules.pmAudio
					settings_dict["response"] = self.__advanceRules.response
					settings_dict["responseNum"] = self.__advanceRules.responseNum
					# Normal Rule Settings
					settings_dict["catch"] = catchList
					settings_dict["avoid"] = avoidList
					file = open("./config/session_settings.toml", "w")
					file.write(tomlkit.dumps(settings_dict))
					file.close()

					rules = BotRules(mode, 
									 evolve, 
									 healThreshold, 
									 speed, 
									 learnMove, 
									 avoidElite, 
									 self.__catchConfigDict, 
									 avoidList,
									 self.__advanceRules)

					self.startSignal.emit(True, rules)
					self.__toggleEnableButtons(False)
			else:
				QMessageBox.question(self, 'Update Catch Rules!', "You need to update the catch rules before starting!", QMessageBox.Ok)
		else:
			self.startSignal.emit(False, None)
			self.__toggleEnableButtons(True)

	def __changeCatchClicked(self):
		pokemonList = []
		for pokemon in range(self.__catchList.count()):
			item = self.__catchList.item(pokemon)
			pokemonList.append(item.text())

		self.__catchSelectionWidget = ListSelectionWidget(pokemonList, "Pokemon To Catch", "Select Pokemon To Catch")
		self.__catchSelectionWidget.listChanges.connect(self.__updateCatchList)
		self.__catchSelectionWidget.show()

	def __changeVoidClicked(self, pokemon):
		pokemonList = []
		for pokemon in range(self.__avoidList.count()):
			item = self.__avoidList.item(pokemon)
			pokemonList.append(item.text())

		self.__avoidSelectionWidget = ListSelectionWidget(pokemonList, "Pokemon To Avoid", "Select Pokemon To Avoid")
		self.__avoidSelectionWidget.listChanges.connect(self.__updateAvoidList)
		self.__avoidSelectionWidget.show()

	def __updateCatchList(self, pokemon):
		self.__catchList.clear()
		for name in pokemon:
			self.__catchList.addItem(name)

		if self.__catchList.count() > 0:
			self.__needUpdateConfig = True
			self.__catchConfigButton.setStyleSheet("background-color: #f67280; color: #000000; font-weight: bold;")
		else:
			self.__needUpdateConfig = False
			if len(self.__catchConfigDict) == 0:
				self.__catchConfigButton.setStyleSheet("background-color: #ffd3b5; color: #000000; font-weight: bold;")
			else:
				self.__catchConfigButton.setStyleSheet("background-color: #7effdb; color: #000000; font-weight: bold;")

	def __updateAvoidList(self, pokemon):
		self.__avoidList.clear()
		for name in pokemon:
			self.__avoidList.addItem(name)

	def __handleAdvanceSettings(self, settings):
		self.__advanceRules = settings

	def handleRunningState(self, state):
		if state:
			self.__startBot.setText("Stop")
		else:
			self.__startBot.setText("Start")
		self.__toggleEnableButtons(not state)

	def __toggleEnableButtons(self, enable):
		self.__botMode.setEnabled(enable)
		self.__learnMove.setEnabled(enable)
		self.__evolveBox.setEnabled(enable)
		self.__eliteBox.setEnabled(enable)
		self.__healSlider.setEnabled(enable)
		self.__speedSlider.setEnabled(enable)
		self.__catchListButton.setEnabled(enable)
		self.__catchConfigButton.setEnabled(enable)
		self.__avoidListButton.setEnabled(enable)
		self.__mouseWalkButton.setEnabled(enable)
		self.__mouseSelectButton.setEnabled(enable)
		self.__advanceSettingsButton.setEnabled(enable)
