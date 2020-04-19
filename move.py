import csv

from type import Type

class Move():

	def __init__(self, id, pp=None, maxpp=None):
		self.id = id
		self.pp = pp
		self.maxpp = maxpp
		self.name = None
		self.power = 0
		self.accuracy = 0
		self.type = None

		self.__setup()

	def __setup(self):
		file = open('csv\\moves.csv')
		movesList = list(csv.DictReader(file, delimiter=','))

		if self.maxpp is None:
			self.maxpp = movesList[self.id - 1]['pp']

		if self.pp is None:
			self.pp = self.maxpp

		self.name = movesList[self.id - 1]['identifier'].replace("-", " ").title()

		if movesList[self.id - 1]['power'] != '':
			self.power = int(movesList[self.id - 1]['power'])
		else:
			self.power = 0


		if movesList[self.id - 1]['accuracy'] != '':
			self.accuracy = int(movesList[self.id - 1]['accuracy'])
		else:
			self.accuracy = 100

		self.type = Type(int(movesList[self.id - 1]['type_id']))