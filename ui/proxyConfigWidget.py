from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QIntValidator
from PySide2.QtWidgets import (QWidget,
							   QDialog,
							   QVBoxLayout,
							   QHBoxLayout,
							   QLabel,
							   QLineEdit, 
							   QPushButton,
							   QComboBox)

import os
import tomlkit
import requests

class ProxyConfigWidget(QDialog):
	proxyUpdate = Signal(object)
	def __init__(self, parent=None):
		super(ProxyConfigWidget, self).__init__(parent)

		self.setAttribute(Qt.WA_DeleteOnClose)
		
		self.setWindowTitle("Proxy Config")


		file = open("./config/client_settings.toml", "r")
		self.clientSettings = tomlkit.parse(file.read())
		file.close()

		proxy_data = self.clientSettings["proxy"]

		self.__mainLayout = QVBoxLayout()

		self.__proxyLabelWidget = QWidget()
		self.__proxyLabelLayout = QHBoxLayout()
		self.__proxyLabelLayout.setMargin(0)
		self.__proxyLabelWidget.setLayout(self.__proxyLabelLayout)

		self.__proxyLabelLayout.addWidget(QLabel("Type"), 25)
		self.__proxyLabelLayout.addWidget(QLabel("Host"), 25)
		self.__proxyLabelLayout.addWidget(QLabel("Port"), 25)
		self.__proxyLabelLayout.addWidget(QLabel("Enabled"), 25)

		self.__proxyInputWidget = QWidget()
		self.__proxyInputLayout = QHBoxLayout()
		self.__proxyInputLayout.addStretch(1)
		self.__proxyInputLayout.setMargin(0)
		self.__proxyInputWidget.setLayout(self.__proxyInputLayout)


		self.__type = QComboBox()
		self.__type.addItems(["http", "socks4", "socks5"])
		self.__host = QLineEdit(proxy_data[2])
		self.__host.setMinimumWidth(100)
		self.__port = QLineEdit(proxy_data[3])
		self.__port.setMinimumWidth(100)
		self.__enabled = QComboBox()
		self.__enabled.addItems(["Enabled", "Disabled"])
		self.__port.setValidator(QIntValidator())

		self.__proxyInputLayout.addWidget(self.__type, 25)
		self.__proxyInputLayout.addWidget(self.__host, 25)
		self.__proxyInputLayout.addWidget(self.__port, 25)
		self.__proxyInputLayout.addWidget(self.__enabled, 25)

		self.__proxyButtonWidget = QWidget()
		self.__proxyButtonLayout = QHBoxLayout()
		self.__proxyButtonLayout.setMargin(0)
		self.__proxyButtonWidget.setLayout(self.__proxyButtonLayout)

		self.__saveButton = QPushButton("Save")
		self.__saveButton.clicked.connect(self.__saveProxyConfig)
		self.__testButton = QPushButton("Test (N/A)")
		self.__testButton.clicked.connect(self.__testProxyConfig)
		self.__proxyButtonLayout.addWidget(self.__testButton)
		self.__proxyButtonLayout.addWidget(self.__saveButton)

		self.__infoLabel = QLabel()
		self.__infoLabel.setAlignment(Qt.AlignCenter)

		if proxy_data[0] == "Disabled":
			self.__enabled.setCurrentIndex(1)

		if proxy_data[1] == "socks5":
			self.__type.setCurrentIndex(2)
		elif proxy_data[1] == "socks4":
			self.__type.setCurrentIndex(1)

		self.__mainLayout.addWidget(self.__proxyLabelWidget)
		self.__mainLayout.addWidget(self.__proxyInputWidget)
		self.__mainLayout.addWidget(self.__proxyButtonWidget)
		self.__mainLayout.addWidget(self.__infoLabel)

		self.setLayout(self.__mainLayout)

		self.__ruleConfigWidget = None

	def __testProxyConfig(self):
		proxy_type = self.__type.currentText()
		proxy_host = self.__host.text()
		proxy_port = self.__port.text()

		if proxy_host == "" or proxy_port == "":
			self.__testButton.setText("Test (FAIL)")
			return False

		self.__testButton.setText("Test (testing...)")
		proxies = {'http': '{}://{}:{}'.format(proxy_type, proxy_host, proxy_port)}
		try:
			req = requests.get("http://pokemon-planet.com", proxies=proxies, timeout=8)
		except:
			self.__testButton.setText("Test (FAIL)")
			return False

		self.__testButton.setText("Test (OK)")
		return True

	def __saveProxyConfig(self):
		self.__infoLabel.setText("...")
		if self.__testProxyConfig():
			proxy_type = self.__type.currentText()
			proxy_host = self.__host.text()
			proxy_port = self.__port.text()
			proxy_enabled = self.__enabled.currentText()

			self.clientSettings["proxy"] = [proxy_enabled, proxy_type, proxy_host, proxy_port]

			file = open("./config/client_settings.toml", "w")
			file.write(tomlkit.dumps(self.clientSettings))
			file.close()
			self.proxyUpdate.emit(self.clientSettings["proxy"])
			self.__infoLabel.setText("SUCCESS: Log out and log back in to apply proxy settings!")
		else:
			self.__infoLabel.setText("ERROR: Cannot save, proxy test failed.")
