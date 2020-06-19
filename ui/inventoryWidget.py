from PySide2.QtWidgets import QDockWidget, QListWidget, QMenu, QAction
from PySide2.QtCore import Signal, Qt, QPoint
from functools import partial

class InventoryWidget(QDockWidget):
	giveItemSignal = Signal(str, int)
	def __init__(self, parent):
		super(InventoryWidget, self).__init__(parent)

		self.setWindowTitle("Inventory")

		self.__contentWidget = QListWidget()
		self.__contentWidget.setContextMenuPolicy(Qt.CustomContextMenu)
		self.__contentWidget.customContextMenuRequested.connect(self.listItemRightClicked)

		self.setWidget(self.__contentWidget)

		self.setFeatures(QDockWidget.DockWidgetMovable)
		self.__contentWidget.setMinimumHeight(200)
		self.__contentWidget.setFixedWidth(200)

	def setInventory(self, items):
		self.__contentWidget.clear()

		for key, value in items.items():
			label = key + ": " + str(value)
			self.__contentWidget.addItem(label)

	def listItemRightClicked(self, QPos):
		if self.__contentWidget.count() > 0:
			self.listMenu = QMenu()
			giveMenu = self.listMenu.addMenu("Give")

			giveOneAction = QAction("Pokemon #1", self)
			giveOneAction.triggered.connect((partial(self.menuItemClicked, 0)))

			giveTwoAction = QAction("Pokemon #2", self)
			giveTwoAction.triggered.connect((partial(self.menuItemClicked, 1)))

			giveThreeAction = QAction("Pokemon #3", self)
			giveThreeAction.triggered.connect((partial(self.menuItemClicked, 2)))

			giveFourAction = QAction("Pokemon #4", self)
			giveFourAction.triggered.connect((partial(self.menuItemClicked, 3)))

			giveFiveAction = QAction("Pokemon #5", self)
			giveFiveAction.triggered.connect((partial(self.menuItemClicked, 4)))

			giveSixAction = QAction("Pokemon #6", self)
			giveSixAction.triggered.connect((partial(self.menuItemClicked, 5)))

			giveMenu.addAction(giveOneAction)
			giveMenu.addAction(giveTwoAction)
			giveMenu.addAction(giveThreeAction)
			giveMenu.addAction(giveFourAction)
			giveMenu.addAction(giveFiveAction)
			giveMenu.addAction(giveSixAction)

			parentPosition = self.__contentWidget.mapToGlobal(QPoint(0, 0))        
			self.listMenu.move(parentPosition + QPos)
			self.listMenu.show() 

	def menuItemClicked(self, pokemon):
		if self.__contentWidget.currentItem() is not None:
		    item_name =str(self.__contentWidget.currentItem().text()).split(":")[0]
		    self.giveItemSignal.emit(item_name, pokemon)