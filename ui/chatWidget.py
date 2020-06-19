import sys
from utils.constants import CONSTANTS

from PySide2.QtCore import Signal
from PySide2.QtGui import QTextCursor
from PySide2.QtWidgets import (QWidget,
                               QTabWidget,
                               QTextEdit,
                               QLineEdit,
                               QVBoxLayout)

class ChatWidget(QWidget):
    sendMessage = Signal(str, str)
    def __init__(self, parent):
        super(ChatWidget, self).__init__(parent)
        self.layout = QVBoxLayout()
        
        # Initialize tab screen
        self.__chatTabs = QTabWidget()
        self.__logTab = QWidget()
        self.__englishTab = QWidget()
        self.__tradingTab = QWidget()
        self.__localTab = QWidget()
        self.__nonEnglishTab = QWidget()
        self.__clanTab = QWidget()
        self.__pmTab = QWidget()

        self.__logChat = QTextEdit()
        self.__logChat.document().setMaximumBlockCount(CONSTANTS.MAX_CHAT_LINES)
        self.__logChat.setReadOnly(True)

        self.__englishChat = QTextEdit()
        self.__englishChat.document().setMaximumBlockCount(CONSTANTS.MAX_CHAT_LINES)
        self.__englishChat.setReadOnly(True)

        self.__tradingChat = QTextEdit()
        self.__tradingChat.document().setMaximumBlockCount(CONSTANTS.MAX_CHAT_LINES)
        self.__tradingChat.setReadOnly(True)

        self.__localChat = QTextEdit()
        self.__localChat.document().setMaximumBlockCount(CONSTANTS.MAX_CHAT_LINES)
        self.__localChat.setReadOnly(True)

        self.__nonEnglishChat = QTextEdit()
        self.__nonEnglishChat.document().setMaximumBlockCount(CONSTANTS.MAX_CHAT_LINES)
        self.__nonEnglishChat.setReadOnly(True)

        self.__clanChat = QTextEdit()
        self.__clanChat.document().setMaximumBlockCount(CONSTANTS.MAX_CHAT_LINES)
        self.__clanChat.setReadOnly(True)

        self.__pmChat = QTextEdit()
        self.__pmChat.document().setMaximumBlockCount(CONSTANTS.MAX_CHAT_LINES)
        self.__pmChat.setReadOnly(True)

        self.__chatInput = QLineEdit()
        self.__chatInput.returnPressed.connect(self.__sendMessage)
        self.__chatTabs.setMinimumSize(400,120)
        
        # Add tabs
        self.__chatTabs.addTab(self.__logTab, "Log")
        self.__chatTabs.addTab(self.__englishTab,"English")
        self.__chatTabs.addTab(self.__tradingTab,"Trading")
        self.__chatTabs.addTab(self.__localTab,"Local")
        self.__chatTabs.addTab(self.__nonEnglishTab,"Non English")
        self.__chatTabs.addTab(self.__clanTab,"Clan")
        self.__chatTabs.addTab(self.__pmTab,"Private")

        
        # Create first tab
        self.__logTabLayout = QVBoxLayout()
        self.__logTabLayout.setMargin(0)
        self.__logTabLayout.addWidget(self.__logChat)
        self.__logTab.setLayout(self.__logTabLayout)

        self.__englishTabLayout = QVBoxLayout()
        self.__englishTabLayout.setMargin(0)
        self.__englishTabLayout.addWidget(self.__englishChat)
        self.__englishTab.setLayout(self.__englishTabLayout)

        self.__tradingTabLayout = QVBoxLayout()
        self.__tradingTabLayout.setMargin(0)
        self.__tradingTabLayout.addWidget(self.__tradingChat)
        self.__tradingTab.setLayout(self.__tradingTabLayout)

        self.__localTabLayout = QVBoxLayout()
        self.__localTabLayout.setMargin(0)
        self.__localTabLayout.addWidget(self.__localChat)
        self.__localTab.setLayout(self.__localTabLayout)

        self.__nonEnglishTabLayout = QVBoxLayout()
        self.__nonEnglishTabLayout.setMargin(0)
        self.__nonEnglishTabLayout.addWidget(self.__nonEnglishChat)
        self.__nonEnglishTab.setLayout(self.__nonEnglishTabLayout)

        self.__clanTabLayout = QVBoxLayout()
        self.__clanTabLayout.setMargin(0)
        self.__clanTabLayout.addWidget(self.__clanChat)
        self.__clanTab.setLayout(self.__clanTabLayout)

        self.__pmTabLayout = QVBoxLayout()
        self.__pmTabLayout.setMargin(0)
        self.__pmTabLayout.addWidget(self.__pmChat)
        self.__pmTab.setLayout(self.__pmTabLayout)

        # Add tabs to widget
        self.layout.addWidget(self.__chatTabs)
        self.layout.addWidget(self.__chatInput)
        self.setLayout(self.layout)

        #self.setStyleSheet("QTextEdit {background: #f1f3f4;}")

    def __sendMessage(self):
        text = self.__chatInput.text()
        self.__chatInput.setText("")

        if text[0] != "@":
            tab = self.__chatTabs.currentIndex()
            if tab == 0 or tab == 1:
                text = "<g>" + text
            elif tab ==2:
                text = "<t>" + text
            elif tab == 3:
                text = "<l>" + text
            elif tab == 4:
                text = "<n>" + text
            elif tab == 5:
                self.sendMessage.emit("<cl>", text)
                return
            else:
                return

            self.sendMessage.emit("", text)
        else:
            text = text.split(" ")
            player = text[0][1:]
            text = " ".join(text[1:])
            self.__pmChat.append("<b>To[" + player + "]</b>: " + text)
            self.__pmChat.ensureCursorVisible()
            self.__chatInput.setText("@" + player + " ")
            self.sendMessage.emit(player.lower(), text)

    def addLog(self, message):
        self.__logChat.append(message)
        self.__logChat.moveCursor(QTextCursor.End)
        self.__logChat.ensureCursorVisible()

    def addMessage(self, user_type, category, user, message):
        completeMessage = "<b>" + user + "</b>" + ": " + message

        font_color = "#FFFFFF";

        if user_type == "<a>":
            font_color = "#FF3737"
        elif user_type == "<z>":
            font_color = "#00FFFF"
        elif user_type == "<x>":
            font_color = "#00FF00"
        elif user_type == "<m>":
            font_color = "#00FF00"
        elif user_type == "<p>":
            font_color = "#FF9900"
        elif user_type == "<s>":
            font_color = "#B382C8"
        elif user_type == "<g>":
            font_color = "#FFCC00"

        completeMessage = "<font color='{}'>{}</font>".format(font_color, completeMessage)
 
        if category == "<g>":
            self.__englishChat.append(completeMessage)
            self.__englishChat.ensureCursorVisible()
        elif category == "<l>":
            self.__localChat.append(completeMessage)
            self.__localChat.moveCursor(QTextCursor.End)
            self.__localChat.ensureCursorVisible()
        elif category == "<t>":
            self.__tradingChat.append(completeMessage)
            self.__tradingChat.moveCursor(QTextCursor.End)
            self.__tradingChat.ensureCursorVisible()
        elif category == "<n>":
            self.__nonEnglishChat.append(completeMessage)
            self.__nonEnglishChat.moveCursor(QTextCursor.End)
            self.__nonEnglishChat.ensureCursorVisible()
        elif category == "<cl>":
            self.__clanChat.append(completeMessage)
            self.__clanChat.moveCursor(QTextCursor.End)
            self.__clanChat.ensureCursorVisible()
        elif category == "<f>":
            self.__pmChat.append(completeMessage)
            self.__pmChat.moveCursor(QTextCursor.End)
            self.__pmChat.ensureCursorVisible()