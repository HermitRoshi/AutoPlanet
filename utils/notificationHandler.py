import threading
from playsound import playsound

from ui.notificationWidget import NotificationWidget
from PySide2.QtCore import QObject

class NotificationHandler(QObject):
	def __init__(self):
		super(NotificationHandler, self).__init__()
		self.__notification = None

	def handleNotification(self, source, popup, audio):
		audio_path = ""
		popup_title = ""
		popup_message = ""

		if source == "trade":
			popup_title = "Trade Request"
			popup_message = "Bot has detected an incoming trade request"
			audio_path = "./data/audio/trade_request.mp3"
		elif source == "battle":
			popup_title = "Battle Request"
			popup_message = "Bot has detected an incoming battle request!"
			audio_path = "./data/audio/battle_request.mp3"
		elif source == "clan":
			popup_title = "Clan Request"
			popup_message = "Bot has detected an incoming clan request!"
			audio_path = "./data/audio/clan_request.mp3"
		elif source == "pm":
			popup_title = "Private Message"
			popup_message = "You have received a private message!"
			audio_path = "./data/audio/private_message.mp3"
		else:
			return

		if audio:
			audio_thread = threading.Thread(target=self.__playSound, args=(audio_path,))
			audio_thread.setDaemon(True)
			audio_thread.start()

		if popup:
			try:
				if self.__notification is not None:
					self.__notification.close()
			except:
				pass

			self.__showPopup(popup_title,popup_message)

	def __playSound(self, path):
		playsound(path)

	def __showPopup(self, title, message):
		self.__notification = NotificationWidget(title, message)
		self.__notification.exec_()
