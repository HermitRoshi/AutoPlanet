from PySide2.QtGui import Qt, QImage, QPixmap
from PySide2.QtWidgets import (QWidget,
							   QDialog,
							   QVBoxLayout,
							   QLabel, 
							   QPushButton)

import requests
import random
from os import path

class NotificationWidget(QDialog):
	def __init__(self, title, message, parent=None):
		super(NotificationWidget, self).__init__(parent)

		self.setAttribute(Qt.WA_DeleteOnClose)
		self.setWindowTitle(title)

		self.setWindowFlags(Qt.WindowStaysOnTopHint)

		self.__mainLayout = QVBoxLayout()
		self.__okButton = QPushButton("Ok")
		self.__okButton.clicked.connect(self.close)

		self.hasNewInfo = False

		self.__helpTextLabel = QLabel(message)
		self.__helpTextLabel.setAlignment(Qt.AlignCenter)

		self.imageLabel = QLabel()
		self.imageLabel.setMaximumHeight(50)
		self.image = QImage("./data/images/pokemon/201-exclamation.png")
		pixmap = QPixmap(self.image)
		scaledPix = pixmap.scaled(self.imageLabel.size(), Qt.KeepAspectRatio, transformMode = Qt.SmoothTransformation)
		self.imageLabel.setAlignment(Qt.AlignCenter)
		self.imageLabel.setPixmap(scaledPix)

		self.__mainLayout.addWidget(self.imageLabel)
		self.__mainLayout.addWidget(self.__helpTextLabel)
		self.__mainLayout.addWidget(self.__okButton)
		self.setLayout(self.__mainLayout)