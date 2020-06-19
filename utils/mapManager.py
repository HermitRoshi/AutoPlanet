import os
import re
import tomlkit
import json

class MapManager():

	def __init__(self):
		self.name = None
		self.region = None
		self.collision = []
		self.cave = False
		self.indoors = False
		self.exits = []
		self.npcs = []

	def __loadMapData(self, filename):
		file = open(filename, "r")
		toml_data = tomlkit.parse(file.read())

		self.name = toml_data["map"]["name"]
		self.region = toml_data["map"]["region"]
		self.collision = json.loads(toml_data["map"]["collision"])
		self.location = toml_data["map"]["location"]
		
		if toml_data["map"]["exits"] != "":
			self.exits = json.loads(toml_data["map"]["exits"])
		else:
			self.exits = []

		if toml_data["map"]["npcs"] != "":
			self.npcs = json.loads(toml_data["map"]["npcs"])
		else:
			self.npcs = []

		# Modify teh collision array to hold NPCs (Tile ID:98)
		for npc in self.npcs:
			self.collision[npc[1]][npc[0]] = 98

	def map(self, name):
		filename = './config/maps/' + name.replace(" ", "_") + ".toml"

		if os.path.exists(filename):
			self.__loadMapData(filename)
			return self.collision
		else:
			return None

	def width(self, name):
		if name == self.name:
			return len(self.collision[0]) - 1
		else:
			return 0

	def height(self, name):
		if name == self.name:
			return len(self.collision) - 1
		else:
			return 0

	def addRocks(self, rocks):
		for rock in rocks:
			if rock[3] == 0:
				self.collision[rock[1]][rock[0]] = 107
			elif rock[2] == "Red":
				self.collision[rock[1]][rock[0]] = 100
			elif rock[2] == "Blue":
				self.collision[rock[1]][rock[0]] = 101
			elif rock[2] == "Green":
				self.collision[rock[1]][rock[0]] = 102
			elif rock[2] == "Prism":
				self.collision[rock[1]][rock[0]] = 103
			elif rock[2] == "Pale":
				self.collision[rock[1]][rock[0]] = 104
			elif rock[2] == "Dark":
				self.collision[rock[1]][rock[0]] = 105
			elif rock[2] == "Rainbow":
				self.collision[rock[1]][rock[0]] = 106
