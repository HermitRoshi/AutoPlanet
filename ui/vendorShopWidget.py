from PySide2.QtCore import Signal, Qt
from PySide2.QtGui import QIntValidator
from PySide2.QtWidgets import (QWidget,
							   QDialog,
							   QVBoxLayout,
							   QGridLayout, 
							   QLabel,
							   QLineEdit, 
							   QPushButton)

import os
import csv
from functools import partial

class VendorShopWidget(QDialog):
	buySignal = Signal(int, int)
	def __init__(self, parent=None):
		super(VendorShopWidget, self).__init__(parent)

		self.setAttribute(Qt.WA_DeleteOnClose)
		
		self.setWindowTitle("Vendor Shop")

		file = open('./data/csv/vendor.csv')
		itemList = list(csv.DictReader(file, delimiter=','))

		self.__items = [None] * len(itemList)

		self.__mainLayout = QVBoxLayout()

		self.__shopLayout = QGridLayout()
		self.__shopLayout.setSpacing(1)
		self.__shopLayout.setMargin(2)
		self.__shopWidget = QWidget()
		self.__shopWidget.setLayout(self.__shopLayout)

		for item in range(len(itemList)):
			item_button = QPushButton(itemList[item]["identifier"])
			item_button.setEnabled(False)
			item_button.setStyleSheet("background-color: #b21f66; color: #FFFFFF; font-weight: bold;")
			item_price = QLabel("Price:   $" + itemList[item]["price"] + "\tQuantity")
			item_quantity = QLineEdit("0")
			item_quantity.setValidator(QIntValidator())
			item_buy = QPushButton("Buy")
			self.__shopLayout.addWidget(item_button, item, 0)
			self.__shopLayout.addWidget(item_price, item, 1)
			self.__shopLayout.addWidget(item_quantity, item, 2)
			self.__shopLayout.addWidget(item_buy, item, 3)
			self.__items[item] = [item_button, item_price, item_quantity, item_buy]
			self.__items[item][3].clicked.connect(partial(self.__buyItem, item))


		self.__mainLayout.addWidget(self.__shopWidget)
		self.setLayout(self.__mainLayout)

		self.__ruleConfigWidget = None

	def __buyItem(self, item):
		''' Sends the signal to buy items

			Resets the buy value as well.
		'''
		count = int(self.__items[item][2].text())
		self.buySignal.emit(item, count)

		self.__items[item][2].setText("0")