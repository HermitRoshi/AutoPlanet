from utils.advanceRules import AdvanceRules

class BotRules(object):
	def __init__(self, mode="Battle", 
						evolve=False,
						healThreshold=0.50,
						speed=3,
						learnMove=4,
						avoidElite=False,
						catchRules=None,
						avoid=[],
						advance=AdvanceRules()):
		self.mode = mode
		self.evolve = evolve
		self.learnMove = learnMove
		self.avoidElite = avoidElite
		self.healThreshold = healThreshold
		self.speed = speed
		self.catchRules = catchRules
		self.avoid = avoid
		self.advance = advance


	def canBattle(self, pokemon):
		""" Returns True if pokemon should be battled

			If the pokemon is to be avoided or caught False is returned
		"""
		if (pokemon.name not in self.avoid and not self.hasCatchRule(pokemon)
			and not (pokemon.elite and self.avoidElite)):
			return True

		return False

	def hasCatchRule(self, pokemon):
		if pokemon.name not in self.catchRules.keys() and not pokemon.shiny:
			return False
		elif pokemon.shiny and "Shiny" in self.catchRules.keys():
			return True
		elif not pokemon.sync and self.catchRules[pokemon.name].sync:
			return False

		return True

	def getCatchRule(self, pokemon):
		if self.hasCatchRule(pokemon):
			if pokemon.name in self.catchRules.keys():
				return self.catchRules[pokemon.name]
			elif pokemon.shiny:
				return self.catchRules["Shiny"]
			else:
				return None
		else:
			return None

	def getUsedPokemon(self):
		""" Get pokemon which will be used in battle.

			Returns an array of pokemon team indicies which will be used
			during battle at some point. Bases used pokemon on catch
			rules. If a pokemon is to be swapped out to be used while
			catching then it is considered a used pokemon.
		"""

		# Start with index 0 as that's the active pokemon
		pokemon_list = [0]

		# Get other pokemon from rules
		for pokemon in self.catchRules:
			if self.catchRules[pokemon].pokemon not in pokemon_list and not self.catchRules[pokemon].stop:
				pokemon_list.append(self.catchRules[pokemon].pokemon)

		return pokemon_list

	def stopCatchLogout(self):
		return self.advance.stopCatchLogout

	def takeLogoutBreak(self):
		return self.advance.takeLogoutBreak

	def fastMine(self):
		return self.advance.fastMine

	def fastFish(self):
		return self.advance.fastFish

	def tradeNotifications(self):
		return [self.advance.tradePopup, self.advance.tradeAudio]

	def battleNotifications(self):
		return [self.advance.battlePopup, self.advance.battleAudio]

	def clanNotifications(self):
		return [self.advance.clanPopup, self.advance.clanAudio]

	def pmNotifications(self):
		return [self.advance.pmPopup, self.advance.pmAudio]