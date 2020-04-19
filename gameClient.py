import sys
import tomlkit

from PySide2.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QWidget
from PySide2.QtCore import Qt

from gameHandler import GameHandler
from ui.chatWidget import ChatWidget
from ui.mapWidget import MapWidget
from ui.accountWidget import AccountWidget
from ui.botControlWidget import BotControlWidget
from ui.teamWidget import TeamWidget
from ui.inventoryWidget import InventoryWidget
from ui.historyWidget import HistoryWidget

class GameClient(QMainWindow):

    def __init__(self, parent=None):
        super(GameClient, self).__init__(parent)
        self.setWindowTitle("Auto Planet")

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
        self.__historyWidget = HistoryWidget(self)

        file = open("./config/client_settings.toml", "r")
        settings_dict = tomlkit.parse(file.read())

        self.__gameHandler = GameHandler(settings_dict["version"],
                                         settings_dict["kg1"],
                                         settings_dict["kg2"],
                                         settings_dict["cf_clearance"],
                                         settings_dict["user_agent"])

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
        self.__gameHandler.historySignal.connect(self.__historyWidget.update)

        self.__botControlWidget.modeSignal.connect(self.__mapWidget.setClickMode)
        self.__botControlWidget.startSignal.connect(self.toggleBot)

        self.setCentralWidget(self.__centralWidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.__accountWidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.__botControlWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.__teamWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.__inventoryWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.__historyWidget)

        self.setStyleSheet("QMainWindow::separator" +
                           "{background: rgb(200, 200, 200);" +
                           "width: 2px; height: 2px;}")

    def login(self, username, password):
        self.__gameHandler.toggleLogin(username, password)

    def toggleBot(self, start, rules):
        if start:
            self.__gameHandler.setRules(self.__mapWidget.getSelectedTiles().copy(), rules)
        else:
            self.__gameHandler.stopBotting()

if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = GameClient()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())
