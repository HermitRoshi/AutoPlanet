import sys

from PySide2.QtCore import Signal, Qt
from PySide2.QtWidgets import (QDockWidget, 
							   QWidget, 
							   QFormLayout, 
							   QLabel, 
							   QLineEdit, 
							   QPushButton,
							   QSizePolicy)

from ui.horizontalLineWidget import HorizontalLineWidget

class AccountWidget(QDockWidget):
	login = Signal(str, str)
	def __init__(self, parent):
		super(AccountWidget, self).__init__(parent)

		self.setWindowTitle("Account")
		self.setFeatures(QDockWidget.DockWidgetMovable)
		self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

		self.__contentWidget = QWidget()
		self.__loginLayout = QFormLayout()
		self.__loginLayout.setMargin(1)
		self.__loginLayout.setSpacing(2)

		self.__contentWidget.setFixedWidth(220)

		self.__accountInfoWidget = QWidget()
		self.__accountInfoLayout = QFormLayout()
		self.__accountInfoLayout.setMargin(0)
		self.__accountInfoWidget.setLayout(self.__accountInfoLayout)

		self.__usernameLabel = QLabel("Username: ")
		self.__passwordLabel = QLabel("Password: ")

		self.__usernameInput = QLineEdit()
		self.__passwordInput = QLineEdit()
		self.__passwordInput.setEchoMode(QLineEdit.Password)

		self.__loginButton = QPushButton("Login")
		self.__loginButton.clicked.connect(self.__sendLogin)

		self.__loginLayout.addRow(self.__usernameLabel, self.__usernameInput)
		self.__loginLayout.addRow(self.__passwordLabel, self.__passwordInput)
		self.__loginLayout.addRow(self.__loginButton)

		self.connectedLabel = QPushButton("Connection: ", objectName='accInfoWidget')
		self.connectedLabel.setEnabled(False)
		self.connectedField = QLineEdit(objectName='accInfoWidget')
		self.connectedField.setAlignment(Qt.AlignRight)
		self.connectedField.setReadOnly(True)
		self.connectedField.setText("DISCONNECTED")
		self.connectedField.setStyleSheet("color: #ad2f02;")
		self.__loginLayout.addRow(self.connectedLabel, self.connectedField)

		self.moneyLabel = QPushButton("Money: ", objectName='accInfoWidget')
		self.moneyLabel.setEnabled(False)
		self.moneyField = QLineEdit(objectName='accInfoWidget')
		self.moneyField.setAlignment(Qt.AlignRight)
		self.moneyField.setReadOnly(True)
		self.moneyField.setText("N/A")
		self.__loginLayout.addRow(self.moneyLabel, self.moneyField)

		self.creditsLabel = QPushButton("Credits: ", objectName='accInfoWidget')
		self.creditsLabel.setEnabled(False)
		self.creditsField = QLineEdit(objectName='accInfoWidget')
		self.creditsField.setAlignment(Qt.AlignRight)
		self.creditsField.setReadOnly(True)
		self.creditsField.setText("N/A")
		self.__loginLayout.addRow(self.creditsLabel, self.creditsField)

		self.mapLabel = QPushButton("Map: ", objectName='accInfoWidget')
		self.mapLabel.setEnabled(False)
		self.mapField = QLineEdit(objectName='accInfoWidget')
		self.mapField.setAlignment(Qt.AlignRight)
		self.mapField.setReadOnly(True)
		self.mapField.setText("N/A")
		self.__loginLayout.addRow(self.mapLabel, self.mapField)

		self.locationLabel = QPushButton("Location: ", objectName='accInfoWidget')
		self.locationLabel.setEnabled(False)
		self.locationField = QLineEdit(objectName='accInfoWidget')
		self.locationField.setAlignment(Qt.AlignRight)
		self.locationField.setReadOnly(True)
		self.locationField.setText("0,0")
		self.__loginLayout.addRow(self.locationLabel, self.locationField)

		self.__contentWidget.setLayout(self.__loginLayout)
		self.setWidget(self.__contentWidget)

		self.setStyleSheet("QPushButton:disabled#accInfoWidget {background-color: #0a64a0; color: #FFFFFF; font-weight: bold;}" +
				   		   "QLineEdit#accInfoWidget {background-color: #d1cebd; color: #424874; font-weight: bold;}")

	def __sendLogin(self):
		username = self.__usernameInput.text()
		password = self.__passwordInput.text()
		self.login.emit(username, password)

	def updateLoginState(self, state):
		if state:
			self.__loginButton.setText("Logout")
			self.connectedField.setText("CONNECTED")
			self.connectedField.setStyleSheet("color: #029631;")
		else:
			self.__loginButton.setText("Login")
			self.connectedField.setText("DISCONNECTED")
			self.connectedField.setStyleSheet("color: #ad2f02;")
			self.moneyField.setText("N/A")
			self.creditsField.setText("N/A")
			self.mapField.setText("N/A")
			self.locationField.setText("0,0")

	def updatePlayerInfo(self, money, credits):
		self.moneyField.setText(str(money))
		self.creditsField.setText(str(credits))

	def updatePositionInfo(self, map, x, y):
		self.mapField.setText(map)
		self.locationField.setText(str(x) + "," + str(y))