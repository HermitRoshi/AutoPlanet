import sys
import tomlkit
import qdarkstyle

from PySide2.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QWidget, QAction, QMenu
from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon

from threading import Thread, Timer

from gameHandler import GameHandler
from ui.helpWidget import HelpWidget
from ui.chatWidget import ChatWidget
from ui.mapWidget import MapWidget
from ui.accountWidget import AccountWidget
from ui.botControlWidget import BotControlWidget
from ui.teamWidget import TeamWidget
from ui.inventoryWidget import InventoryWidget
from ui.sessionWidget import SessionWidget
from ui.vendorShopWidget import VendorShopWidget
from ui.announcementWidget import AnnouncementWidget
from ui.proxyConfigWidget import ProxyConfigWidget
from ui.loadLocationWidget import LoadLocationWidget
from ui.globalMarketplaceWidget import GlobalMarketplaceWidget

class GameClient(QMainWindow):

    def __init__(self, parent=None):
        super(GameClient, self).__init__(parent)
        self.setWindowTitle("Auto Planet 0.9.9")
        self.setWindowIcon(QIcon("./data/images/pokeball.png"))

        self.__announcementShown = False

        self.__centralWidgetLayout = QVBoxLayout()
        self.__centralWidgetLayout.setMargin(0)
        self.__centralWidget = QWidget()


        self.__mapWidget = MapWidget(self)
        self.__chatWidget = ChatWidget(self)
        self.__centralWidgetLayout.addWidget(self.__mapWidget)
        self.__centralWidgetLayout.addWidget(self.__chatWidget)
        self.__centralWidget.setLayout(self.__centralWidgetLayout)

        self.__accountWidget = AccountWidget(self)
        self.__accountWidget.login.connect(self.login)
        self.__botControlWidget = BotControlWidget(self)
        self.__teamWidget = TeamWidget(self)
        self.__inventoryWidget = InventoryWidget(self)
        self.__sessionWidget = SessionWidget(self)

        file = open("./config/client_settings.toml", "r")
        settings_dict = tomlkit.parse(file.read())

        self.__gameHandler = GameHandler(settings_dict["version"],
                                         settings_dict["kg1"],
                                         settings_dict["kg2"],
                                         settings_dict["cf_clearance"],
                                         settings_dict["user_agent"],
                                         settings_dict["proxy"])

        self.__chatWidget.sendMessage.connect(self.__gameHandler.sendPmsg)
        self.__mapWidget.walkCommandSignal.connect(self.__gameHandler.walkCommand)

        self.__gameHandler.chatSignal.connect(self.__chatWidget.addMessage)
        self.__gameHandler.teamSignal.connect(self.__teamWidget.setTeam)
        self.__gameHandler.inventorySignal.connect(self.__inventoryWidget.setInventory)
        self.__gameHandler.positionSignal.connect(self.__mapWidget.updatePosition)
        self.__gameHandler.logSignal.connect(self.__chatWidget.addLog)
        self.__gameHandler.connectedSignal.connect(self.__accountWidget.updateLoginState)
        self.__gameHandler.infoSignal.connect(self.__accountWidget.updatePlayerInfo)
        self.__gameHandler.positionSignal.connect(self.__accountWidget.updatePositionInfo)
        self.__gameHandler.mountChanged.connect(self.__mapWidget.setMount)
        self.__gameHandler.historySignal.connect(self.__sessionWidget.update)
        self.__gameHandler.rockSignal.connect(self.__mapWidget.addRocks)
        self.__gameHandler.runningSignal.connect(self.__botControlWidget.handleRunningState)
        self.__gameHandler.playersSignal.connect(self.__sessionWidget.updatePlayers)

        self.__botControlWidget.modeSignal.connect(self.__mapWidget.setClickMode)
        self.__botControlWidget.startSignal.connect(self.toggleBot)

        self.__teamWidget.reorderSignal.connect(self.teamReorder)
        self.__teamWidget.removeItemSignal.connect(self.__gameHandler.removeItem)

        self.__inventoryWidget.giveItemSignal.connect(self.__gameHandler.giveItem)

        self.setCentralWidget(self.__centralWidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.__accountWidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.__botControlWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.__teamWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.__inventoryWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.__sessionWidget)

        self.__setupMenubar()

        self.setStyleSheet("QMainWindow::separator" +
                           "{background: rgb(200, 200, 200);" +
                           "width: 2px; height: 2px;}")

    def showEvent(self, event):
        if not self.__announcementShown:
            announcement = AnnouncementWidget()
            if announcement.hasNewInfo:
                announcement.exec()
            self.__announcementShown = True

    def __setupMenubar(self):
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        accessMenu = mainMenu.addMenu('Access')
        optionsMenu = mainMenu.addMenu('Options')
        helpMenu = mainMenu.addMenu('Help')

        quitAction = QAction("Quit", self)
        quitAction.setShortcut("Ctrl+Q")
        quitAction.setStatusTip('Close Auto Planet')
        quitAction.triggered.connect(self.close)
        fileMenu.addAction(quitAction)

        proxyAction = QAction("Proxy", self)
        proxyAction.setStatusTip('Proxy for web and game connection')
        proxyAction.triggered.connect(self.__manageProxy)
        optionsMenu.addAction(proxyAction)

        helpAction = QAction("How To Use", self)
        helpAction.setStatusTip('Botting help')
        helpAction.triggered.connect(self.__showHelp)
        helpMenu.addAction(helpAction)

        shopMenu = accessMenu.addMenu("Shop")
        locationMenu = accessMenu.addMenu("Location")

        vendorShopAction = QAction("Vendor Shop", self)
        vendorShopAction.triggered.connect(self.__showVendorShop)
        shopMenu.addAction(vendorShopAction)

        globalMarketplaceAction = QAction("Global Marketplace", self)
        globalMarketplaceAction.triggered.connect(self.__showGlobalMarketplace)
        shopMenu.addAction(globalMarketplaceAction)

        loadLocationAction = QAction("Load Location", self)
        loadLocationAction.triggered.connect(self.__showLoadLocation)
        locationMenu.addAction(loadLocationAction)

    def login(self, username, password):
        self.__gameHandler.toggleLogin(username, password)

    def toggleBot(self, start, rules):
        if start:
            self.__gameHandler.setRules(self.__mapWidget.getSelectedTiles().copy(), rules)
        else:
            self.__gameHandler.stopBotting()

    def teamReorder(self, move_from, move_to):
        self.__gameHandler.handlePokemonReorder(move_from, move_to)

    def __showLoadLocation(self):
        loadLocation = LoadLocationWidget()
        loadLocation.loadLocationSignal.connect(self.__gameHandler.setLocation)
        loadLocation.exec_()

    def __manageProxy(self):
        proxyConfig = ProxyConfigWidget()
        proxyConfig.proxyUpdate.connect(self.__updateProxy)
        proxyConfig.exec_()

    def __updateProxy(self, proxy):
        self.__gameHandler.updateProxy(proxy)

    def __showVendorShop(self):
        vendorShop = VendorShopWidget()
        vendorShop.buySignal.connect(self.__gameHandler.handleVendorBuy)
        vendorShop.exec_()

    def __showGlobalMarketplace(self):
        globalMarketplace = GlobalMarketplaceWidget()
        globalMarketplace.searchSignal.connect(self.__gameHandler.searchMarketplace)
        globalMarketplace.buySignal.connect(self.__gameHandler.buyMarketplace)
        self.__gameHandler.globalMarketplace.connect(globalMarketplace.searchResults)
        globalMarketplace.exec_()

    def __showAnnouncement(self):
        self.announcement = AnnouncementWidget()
        self.announcement.show()

    def __showHelp(self):
        helpWindow = HelpWidget()
        helpWindow.exec_()
        
if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = GameClient()
    # setup stylesheet
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyside2())
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())
