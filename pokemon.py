import math
import csv
import ast
from move import Move
from ability import Ability
from type import Type

class Pokemon():

	def __init__(self, dataString):
		data = dataString.split(',')

		self.uuid = int(data[0])
		self.happiness = int(data[1])
		self.specDef = int(data[2])
		self.specAtk = int(data[3])
		self.speed = int(data[4])
		self.defense = int(data[5])
		self.attack = int(data[6])
		self.health = int(data[7])
		self.specDefEV = int(data[8])
		self.specAtkEV = int(data[9])
		self.speedEV = int(data[10])
		self.defenseEV = int(data[11])
		self.attackEV = int(data[12])
		self.healthEV = int(data[13])
		self.specDefIV = int(data[14])
		self.specAtkIV = int(data[15])
		self.speedIV = int(data[16])
		self.defenseIV = int(data[17])
		self.attackIV = int(data[18])
		self.healthIV = int(data[19])
		self.nature = data[20]

		self.moves = []
		if int(data[21]) != 0:
			self.moves.append(Move(int(data[21])))
		if int(data[22]) != 0:
			self.moves.append(Move(int(data[22])))
		if int(data[23]) != 0:
			self.moves.append(Move(int(data[23])))
		if int(data[24]) != 0:
			self.moves.append(Move(int(data[24])))
		self.type = Type(int(data[26]))
		self.type2 = Type(int(data[25]))
		self.currentHealth = int(data[27])
		self.totalExperience = int(data[28])
		self.levelExperience = int(data[29])
		self.shiny = str(data[30]) == 'true'
		self.level = int(data[31])
		self.id = int(data[32])
		self.name = str(data[33])
		self.item = str(data[34])
		self.ability = Ability(int(data[35]))
		self.ailment = data[36]
		self.catcher = str(data[38])

	def expForNextLevel(self):
		return (math.floor(0.550000 * (self.level * self.level * self.level * (self.level / 35 - 0.100000))) + 120 + self.level * 20)

	def getHpPercent(self):
		return self.currentHealth / self.health


class WildPokemon():

	def __init__(self, dataString):
		all_data = dataString.split('`')
		data = all_data[4].split(",")
		self.currentHp = int(data[0])
		self.maxHp = int(data[1])
		self.name = str(data[2])
		self.id = int(data[3])
		self.shiny = data[4] == "true"
		self.level = int(data[5])
		self.ability = Ability(data[6], encoded=True)
		self.ailment = data[7]
		self.form = data[8]
		self.elite = data[9] == "true"
		self.type = Type(int(data[10]))
		self.type2 = Type(int(data[11]))

		# Breaking up the multiple arrays. Messy manual work. TODO
		boost_data = all_data[14].replace("[[","[").replace("]]", "]").replace("],[", "], [").split(", ")
		if boost_data[4] != "[NaN]":
			self.sync = int(ast.literal_eval(boost_data[4])[0]) == 1
		else:
			self.sync = False

		file = open('./data/csv/effect.csv')
		reader = csv.DictReader(file, delimiter=',')
		self.effectDict={}

		for row in reader:
			if row['damage_type_id'] in self.effectDict:
				self.effectDict[row['damage_type_id']].append(row['damage_factor'])
			else:
				self.effectDict[row['damage_type_id']] = [row['damage_factor']]

	def updateFromCMessage(self, dataString):
		data = dataString.split(",")
		self.ailment = data[1]
		self.name = data[4]
		self.currentHp = int(data[9])
		self.mapHp = int(data[8])

	def getEffectiveness(self, damageType):
		type_one = int(self.effectDict[str(damageType)][int(self.type.id) - 1])/100

		if self.type2.id == 0:
			return type_one
		else:
			return type_one * (int(self.effectDict[str(damageType)][int(self.type2.id) - 1])/100)

	def getHpPercent(self):
		return int((self.currentHp / self.maxHp) * 100)