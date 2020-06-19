from PySide2.QtGui import Qt, QImage, QPixmap
from PySide2.QtCore import QSize
from PySide2.QtWidgets import (QWidget,
							   QDialog,
							   QVBoxLayout,
							   QLabel, 
							   QPushButton)

import requests
import random
from os import path

class AnnouncementWidget(QDialog):
	def __init__(self, parent=None):
		super(AnnouncementWidget, self).__init__(parent)

		self.setAttribute(Qt.WA_DeleteOnClose)
		self.setWindowTitle("Announcement")

		self.__mainLayout = QVBoxLayout()
		self.__okButton = QPushButton("Ok")
		self.__okButton.clicked.connect(self.close)

		self.hasNewInfo = False

		announcement_text = ''
		try:
			announcement_text = requests.get("http://pastebin.com/raw/8S56MX8H", timeout=5).text
		except:
			announcement_text = 'ERROR: Cannot get latest announcement'
			self.hasNewInfo = True

		if path.exists('config\\announcement.txt'):
			file = open('config\\announcement.txt')
			old_text = file.read()
			if old_text.strip() != announcement_text.replace('\r',''):
				self.hasNewInfo = True
		else:
			self.hasNewInfo = True

		if self.hasNewInfo:
			file = open('config\\announcement.txt', 'w')
			file.write(announcement_text.replace('\r',''))

		self.__announcementWidget = QLabel(announcement_text)
		self.__announcementWidget.setTextInteractionFlags(Qt.TextBrowserInteraction)
		self.__announcementWidget.setOpenExternalLinks(True)

		self.imageLabel = QLabel()
		self.imageLabel.setMaximumHeight(150)
		self.image = QImage("./data/images/pokemon/" + str(random.randint(1, 649)) + ".png")
		pixmap = QPixmap(self.image)
		scaledPix = pixmap.scaled(self.imageLabel.size(), Qt.KeepAspectRatio, transformMode = Qt.SmoothTransformation)
		self.imageLabel.setAlignment(Qt.AlignCenter)
		self.imageLabel.setPixmap(scaledPix)

		self.__mainLayout.addWidget(self.imageLabel)
		self.__mainLayout.addWidget(self.__announcementWidget)
		self.__mainLayout.addWidget(self.__okButton)
		self.setLayout(self.__mainLayout)