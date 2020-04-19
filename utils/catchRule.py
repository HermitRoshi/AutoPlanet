
class CatchRule():

	def __init__(self, name, stop, pokemon, move, status, health, pokeball):
		self.name = name
		self.stop = stop
		self.pokemon = pokemon
		self.move = move
		self.status = status.lower()
		self.health = health
		self.pokeball = pokeball