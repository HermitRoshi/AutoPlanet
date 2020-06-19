from PySide2.QtGui import Qt, QImage, QPixmap, QIntValidator
from PySide2.QtCore import Signal
from PySide2.QtWidgets import (QWidget,
							   QDialog,
							   QHBoxLayout,
							   QLabel, 
							   QPushButton,
							   QTabWidget,
							   QFormLayout,
							   QGridLayout,
							   QComboBox,
							   QCheckBox,
							   QLineEdit)

import requests
import random
from utils.advanceRules import AdvanceRules
from os import path

class AdvanceSettingsWidget(QDialog):
	settingsSavedSignal = Signal(object)
	def __init__(self, settings, parent=None):
		super(AdvanceSettingsWidget, self).__init__(parent)

		self.setAttribute(Qt.WA_DeleteOnClose)
		self.setWindowTitle("Advance Settings")

		self.__mainLayout = QFormLayout()
		self.__settingsTabs = QTabWidget()
		self.__generalLayout = QGridLayout()
		self.__socialLayout = QGridLayout()

		self.__generalTab = QWidget()
		self.__generalTab.setLayout(self.__generalLayout)
		self.__socialTab = QWidget()
		self.__socialTab.setLayout(self.__socialLayout)

		self.__settingsTabs.addTab(self.__generalTab, "General")
		self.__settingsTabs.addTab(self.__socialTab, "Social")
		self.__generalLayout.addWidget

		# General tab settings
		self.__stopCatchLabel = QLabel("Stop Catch Rule: ")
		self.__stopCatchCombo = QComboBox()
		self.__stopCatchCombo.addItems(["Logout", "Wait"])
		if not settings.stopCatchLogout:
			self.__stopCatchCombo.setCurrentIndex(1)
		self.__generalLayout.addWidget(self.__stopCatchLabel, 0, 0)
		self.__generalLayout.addWidget(self.__stopCatchCombo, 0, 1)

		self.__logoutBreakLabel = QLabel("Take logout breaks: ")
		self.__logoutBreakCombo = QComboBox()
		self.__logoutBreakCombo.addItems(["No", "Yes"])
		if settings.takeLogoutBreak:
			self.__logoutBreakCombo.setCurrentIndex(1)
		self.__generalLayout.addWidget(self.__logoutBreakLabel, 1, 0)
		self.__generalLayout.addWidget(self.__logoutBreakCombo, 1, 1)

		self.__experimentalLabel = QLabel("Settings below are experimental and pose a higher ban risk.")
		self.__generalLayout.addWidget(self.__experimentalLabel, 2, 0)

		self.__fastFishingLabel = QLabel("Higher fishing success rate: ")
		self.__fastFishingCombo = QComboBox()
		self.__fastFishingCombo.addItems(["No", "Yes"])
		if settings.fastFish:
			self.__fastFishingCombo.setCurrentIndex(1)
		self.__generalLayout.addWidget(self.__fastFishingLabel, 3, 0)
		self.__generalLayout.addWidget(self.__fastFishingCombo, 3, 1)

		self.__fastMiningLabel = QLabel("Higher mining success rate: ")
		self.__fastMiningCombo = QComboBox()
		self.__fastMiningCombo.addItems(["No", "Yes"])
		if settings.fastMine:
			self.__fastMiningCombo.setCurrentIndex(1)
		self.__generalLayout.addWidget(self.__fastMiningLabel, 4, 0)
		self.__generalLayout.addWidget(self.__fastMiningCombo, 4, 1)

		# Social tab settings
		self.__tradeRequestLabel = QLabel("Trade request notification: ")
		self.__tradeRequestPopupBox = QCheckBox("Pop-up", self)
		if settings.tradePopup:
			self.__tradeRequestPopupBox.setChecked(True)
		self.__tradeRequestAudioBox = QCheckBox("Audio", self)
		if settings.tradeAudio:
			self.__tradeRequestAudioBox.setChecked(True)
		self.__socialLayout.addWidget(self.__tradeRequestLabel, 0, 0)
		self.__socialLayout.addWidget(self.__tradeRequestPopupBox, 0, 1)
		self.__socialLayout.addWidget(self.__tradeRequestAudioBox, 0, 2)

		self.__battleRequestLabel = QLabel("Battle request notification: ")
		self.__battleRequestPopupBox = QCheckBox("Pop-up", self)
		if settings.battlePopup:
			self.__battleRequestPopupBox.setChecked(True)
		self.__battleRequestAudioBox = QCheckBox("Audio", self)
		if settings.battleAudio:
			self.__battleRequestAudioBox.setChecked(True)
		self.__socialLayout.addWidget(self.__battleRequestLabel, 1, 0)
		self.__socialLayout.addWidget(self.__battleRequestPopupBox, 1, 1)
		self.__socialLayout.addWidget(self.__battleRequestAudioBox, 1, 2)


		self.__clanRequestLabel = QLabel("Clan request notification: ")
		self.__clanRequestPopupBox = QCheckBox("Pop-up", self)
		if settings.clanPopup:
			self.__clanRequestPopupBox.setChecked(True)
		self.__clanRequestAudioBox = QCheckBox("Audio", self)
		if settings.clanAudio:
			self.__clanRequestAudioBox.setChecked(True)
		self.__socialLayout.addWidget(self.__clanRequestLabel, 2, 0)
		self.__socialLayout.addWidget(self.__clanRequestPopupBox, 2, 1)
		self.__socialLayout.addWidget(self.__clanRequestAudioBox, 2, 2)

		self.__pmRequestLabel = QLabel("Private message notification: ")
		self.__pmRequestPopupBox = QCheckBox("Pop-up", self)
		if settings.pmPopup:
			self.__pmRequestPopupBox.setChecked(True)
		self.__pmRequestAudioBox = QCheckBox("Audio", self)
		if settings.pmAudio:
			self.__pmRequestAudioBox.setChecked(True)
		self.__socialLayout.addWidget(self.__pmRequestLabel, 3, 0)
		self.__socialLayout.addWidget(self.__pmRequestPopupBox, 3, 1)
		self.__socialLayout.addWidget(self.__pmRequestAudioBox, 3, 2)

		self.__socialLayout.addWidget(QLabel("Request responses(comma delimit for multiple)"), 4, 0)
		self.__socialLayout.addWidget(QLabel("After # Requests"), 4, 1)

		self.__requestResponseLineEdit = QLineEdit(settings.response)
		self.__requestResponseNumLineEdit = QLineEdit(settings.responseNum)
		self.__requestResponseNumLineEdit.setValidator(QIntValidator())
		self.__socialLayout.addWidget(self.__requestResponseLineEdit, 5, 0)
		self.__socialLayout.addWidget(self.__requestResponseNumLineEdit, 5, 1)

		self.__saveButton = QPushButton("Save")
		self.__saveButton.clicked.connect(self.__save)
		self.__resetButton = QPushButton("Reset")

		self.__mainLayout.addRow(self.__settingsTabs)
		self.__mainLayout.addRow(self.__resetButton, self.__saveButton)
		self.setLayout(self.__mainLayout)

	def __save(self):
		# General Rules
		stop_catch_logout = self.__stopCatchCombo.currentText() == "Logout"
		take_logout_break = self.__logoutBreakCombo.currentText() == "Yes"
		fast_fish = self.__fastFishingCombo.currentText() == "Yes"
		fast_mine = self.__fastMiningCombo.currentText() == "Yes"

		# Social Rules
		trade_popup = self.__tradeRequestPopupBox.isChecked()
		trade_audio = self.__tradeRequestAudioBox.isChecked()
		battle_popup = self.__battleRequestPopupBox.isChecked()
		battle_audio = self.__battleRequestAudioBox.isChecked()
		clan_popup = self.__clanRequestPopupBox.isChecked()
		clan_audio = self.__clanRequestAudioBox.isChecked()
		pm_popup = self.__pmRequestPopupBox.isChecked()
		pm_audio = self.__pmRequestAudioBox.isChecked()
		response = self.__requestResponseLineEdit.text()
		response_num = self.__requestResponseNumLineEdit.text()

		advance_rules = AdvanceRules()
		advance_rules.setGeneralSettings(stop_catch_logout,
										 take_logout_break,
										 fast_fish,
										 fast_mine)
		advance_rules.setSocialSettings(trade_popup,
										 trade_audio,
										 battle_popup,
										 battle_audio,
										 clan_popup,
										 clan_audio,
										 pm_popup,
										 pm_audio,
										 response,
										 response_num)

		self.settingsSavedSignal.emit(advance_rules)
		self.close()