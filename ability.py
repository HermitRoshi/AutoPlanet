import csv
from utils.utils import stringToMd5
class Ability():

	def __init__(self, id, encoded=False):
		self.id = id
		self.name = None

		self.__setup(encoded)

	def __setup(self, encoded):
		file = open('csv\\abilities.csv')
		abilityList = list(csv.DictReader(file, delimiter=','))

		crypto_key = "asion1asfonapsfobq1n12iofrasnfra"

		if encoded:
			for ability in range(len(abilityList)):
				if stringToMd5(str(ability) + crypto_key) == self.id:
					self.id = int(ability)
					self.name = abilityList[ability-1]['identifier'].replace("-", " ").title()
					break
		else:
			self.name = abilityList[self.id - 1]['identifier'].replace("-", " ").title()