import csv

class Type():

	def __init__(self, id):
		self.id = id
		self.name = None

		if id != 0:
			self.__setup()

	def __setup(self):
		file = open('csv\\types.csv')
		typeList = list(csv.DictReader(file, delimiter=','))

		self.name = typeList[self.id - 1]['identifier'].replace("-", " ").title()