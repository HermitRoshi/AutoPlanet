class AdvanceRules():
	def __init__(self):
		# General Settings
		self.stopCatchLogout = True
		self.takeLogoutBreak = False
		self.fastFish = False
		self.fastMine = False

		# Social Settings
		self.tradePopup = False
		self.tradeAudio = False
		self.battlePopup = False
		self.battleAudio = False
		self.clanPopup = False
		self.clanAudio = False
		self.pmPopup = False
		self.pmAudio = False
		self.response = ""
		self.responseNum = "0"

	def setGeneralSettings(self, stopCatchLogout=True, 
								 takeLogoutBreak=False, 
								 fastFish=False, 
								 fastMine=False):
		self.stopCatchLogout = stopCatchLogout
		self.takeLogoutBreak = takeLogoutBreak
		self.fastFish = fastFish
		self.fastMine = fastMine


	def setSocialSettings(self, tradePopup = False, 
								tradeAudio = False, 
								battlePopup = False, 
								battleAudio = False, 
								clanPopup = False, 
								clanAudio = False, 
								pmPopup = False, 
								pmAudio = False,
								response = "",
								responseNum = 0):
		self.tradePopup = tradePopup
		self.tradeAudio = tradeAudio
		self.battlePopup = battlePopup
		self.battleAudio = battleAudio
		self.clanPopup = clanPopup
		self.clanAudio = clanAudio
		self.pmPopup = pmPopup
		self.pmAudio = pmAudio
		self.response = response
		self.responseNum = str(responseNum)
