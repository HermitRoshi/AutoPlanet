from PySide2.QtGui import Qt, QImage, QPixmap
from PySide2.QtWidgets import (QWidget,
							   QDialog,
							   QVBoxLayout,
							   QLabel, 
							   QPushButton)

import requests
import random
from os import path

class HelpWidget(QDialog):
	def __init__(self, parent=None):
		super(HelpWidget, self).__init__(parent)

		self.setAttribute(Qt.WA_DeleteOnClose)
		self.setWindowTitle("Help")

		self.__mainLayout = QVBoxLayout()
		self.__okButton = QPushButton("Ok")
		self.__okButton.clicked.connect(self.close)

		self.hasNewInfo = False

		help_text =("Auto Planet v0.9.9 <br>" +
					"Author: Goku <br>" +
					"Discord: <a href=\"https://discord.gg/rbAwPpC\">https://discord.gg/rbAwPpC</a> <br> <br>" +
					"For help, bug reports, suggestions, and latest updates visit the discord!")

		self.__helpTextLabel = QLabel(help_text)
		self.__helpTextLabel.setAlignment(Qt.AlignCenter)
		self.__helpTextLabel.setTextInteractionFlags(Qt.TextBrowserInteraction)
		self.__helpTextLabel.setOpenExternalLinks(True)

		self.imageLabel = QLabel()
		self.imageLabel.setMaximumHeight(100)
		self.image = QImage("./data/images/pokemon/egg.png")
		pixmap = QPixmap(self.image)
		scaledPix = pixmap.scaled(self.imageLabel.size(), Qt.KeepAspectRatio, transformMode = Qt.SmoothTransformation)
		self.imageLabel.setAlignment(Qt.AlignCenter)
		self.imageLabel.setPixmap(scaledPix)

		self.__mainLayout.addWidget(self.imageLabel)
		self.__mainLayout.addWidget(self.__helpTextLabel)
		self.__mainLayout.addWidget(self.__okButton)
		self.setLayout(self.__mainLayout)