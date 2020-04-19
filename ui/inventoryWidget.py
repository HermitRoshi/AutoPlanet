import sys

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

class InventoryWidget(QDockWidget):
	def __init__(self, parent):
		super(InventoryWidget, self).__init__(parent)

		self.setWindowTitle("Inventory")

		self.__contentWidget = QListWidget()

		self.setWidget(self.__contentWidget)

		self.setFeatures(QDockWidget.DockWidgetMovable)
		self.__contentWidget.setMinimumHeight(250)
		self.__contentWidget.setMaximumSize(200,274)


	def setInventory(self, items):
		self.__contentWidget.clear()

		for key, value in items.items():
			label = key + ": " + str(value)
			self.__contentWidget.addItem(label)