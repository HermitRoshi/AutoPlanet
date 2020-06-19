from PySide2.QtWidgets import QDialog, QFormLayout, QWidget, QLabel, QPushButton, QLineEdit, QHBoxLayout
from PySide2.QtCore import QSize, Signal
from PySide2.QtGui import Qt, QImage, QPixmap

from pokemon import Pokemon
from functools import partial

class PokemonDetailsWidget(QDialog):
	reorderSignal = Signal(int, int)
	def __init__(self, pokemon, widget_id, parent=None):
		super(PokemonDetailsWidget, self).__init__(parent)
		self.widget_id = widget_id
		self.setAttribute(Qt.WA_DeleteOnClose)
		
		self.setStyleSheet("QPushButton {background-color: #b21f66; color: #FFFFFF; font-weight: bold;}" +
						   "QLineEdit {background-color: #d1cebd; color: #424874; font-weight: bold; width: 110px;}")
		self.setWindowTitle(pokemon.name.title())
		self.mainLayout = QFormLayout()
		self.leftWidget = QWidget()
		self.rightWidget = QWidget()
		self.statsLayout = QFormLayout()
		self.statsLayout.setSpacing(1)
		self.leftLayout = QFormLayout()
		self.leftLayout.setSpacing(1)
		self.slotWidget = QWidget()
		self.slotLayout = QHBoxLayout()


		self.imageLabel = QLabel()
		self.imageLabel.setFixedSize(QSize(200, 135))
		self.image = QImage("./data/images/pokemon/" + str(pokemon.id) + ".png")
		pixmap = QPixmap(self.image)
		scaledPix = pixmap.scaled(self.imageLabel.size(), Qt.KeepAspectRatio, transformMode = Qt.SmoothTransformation)
		self.imageLabel.setAlignment(Qt.AlignCenter)
		self.imageLabel.setPixmap(scaledPix)
		self.leftLayout.addRow(self.imageLabel)


		self.nameLabel = QPushButton("Name: ")
		self.nameLabel.setEnabled(False)
		self.nameField = QLineEdit()
		self.nameField.setAlignment(Qt.AlignRight)
		self.nameField.setReadOnly(True)
		self.nameField.setText(str(pokemon.name))
		self.leftLayout.addRow(self.nameLabel, self.nameField)

		self.levelLabel = QPushButton("Level: ")
		self.levelLabel.setEnabled(False)
		self.levelField = QLineEdit()
		self.levelField.setAlignment(Qt.AlignRight)
		self.levelField.setReadOnly(True)
		self.levelField.setText(str(pokemon.level))
		self.leftLayout.addRow(self.levelLabel, self.levelField)

		self.itemLabel = QPushButton("Item: ")
		self.itemLabel.setEnabled(False)
		self.itemField = QLineEdit()
		self.itemField.setAlignment(Qt.AlignRight)
		self.itemField.setReadOnly(True)
		self.itemField.setText(str(pokemon.item))
		self.leftLayout.addRow(self.itemLabel, self.itemField)

		for move in pokemon.moves:
			moveLabel = QPushButton("Move: ")
			moveLabel.setEnabled(False)
			moveField = QLineEdit()
			moveField.setAlignment(Qt.AlignRight)
			moveField.setReadOnly(True)
			moveField.setText(str(move.name))
			moveField.setToolTip("Type: {} | Power: {} | Accuracy: {}".format(move.type.name, move.power, move.accuracy))
			self.leftLayout.addRow(moveLabel, moveField)


		self.pokedexLabel = QPushButton("Pokedex: ")
		self.pokedexLabel.setEnabled(False)
		self.pokedexField = QLineEdit()
		self.pokedexField.setAlignment(Qt.AlignRight)
		self.pokedexField.setReadOnly(True)
		self.pokedexField.setText(str(pokemon.id))
		self.statsLayout.addRow(self.pokedexLabel, self.pokedexField)

		self.typeLabel = QPushButton("Type: ")
		self.typeLabel.setEnabled(False)
		self.typeField = QLineEdit()
		self.typeField.setAlignment(Qt.AlignRight)
		self.typeField.setReadOnly(True)
		typeString = str(pokemon.type.name).title()
		if pokemon.type2.name is not None:
			typeString = typeString + "/" + str(pokemon.type2.name).title()
		self.typeField.setText(typeString)
		self.statsLayout.addRow(self.typeLabel, self.typeField)

		self.natureLabel = QPushButton("Nature: ")
		self.natureLabel.setEnabled(False)
		self.natureField = QLineEdit()
		self.natureField.setAlignment(Qt.AlignRight)
		self.natureField.setReadOnly(True)
		self.natureField.setText(str(pokemon.nature).title())
		self.statsLayout.addRow(self.natureLabel, self.natureField)

		self.happinessLabel = QPushButton("Happiness: ")
		self.happinessLabel.setEnabled(False)
		self.happinessField = QLineEdit()
		self.happinessField.setAlignment(Qt.AlignRight)
		self.happinessField.setReadOnly(True)
		self.happinessField.setText(str(pokemon.happiness))
		self.statsLayout.addRow(self.happinessLabel, self.happinessField)

		self.abilityLabel = QPushButton("Ability: ")
		self.abilityLabel.setEnabled(False)
		self.abilityField = QLineEdit()
		self.abilityField.setAlignment(Qt.AlignRight)
		self.abilityField.setReadOnly(True)
		self.abilityField.setText(str(pokemon.ability.name).title())
		self.statsLayout.addRow(self.abilityLabel, self.abilityField)

		self.catcherLabel = QPushButton("Catcher: ")
		self.catcherLabel.setEnabled(False)
		self.catcherField = QLineEdit()
		self.catcherField.setAlignment(Qt.AlignRight)
		self.catcherField.setReadOnly(True)
		self.catcherField.setText("HIDDEN")
		self.statsLayout.addRow(self.catcherLabel, self.catcherField)

		self.hpLabel = QPushButton("Hp: ")
		self.hpLabel.setEnabled(False)
		self.hpField = QLineEdit()
		self.hpField.setAlignment(Qt.AlignRight)
		self.hpField.setReadOnly(True)
		self.hpField.setText(str(pokemon.currentHealth) + "/" + str(pokemon.health) + " IV:" + str(pokemon.healthIV) + " EV:" + str(pokemon.healthEV))
		self.statsLayout.addRow(self.hpLabel, self.hpField)

		self.expLabel = QPushButton("Exp: ")
		self.expLabel.setEnabled(False)
		self.expField = QLineEdit()
		self.expField.setAlignment(Qt.AlignRight)
		self.expField.setReadOnly(True)
		self.expField.setText(str(pokemon.levelExperience) + "/" + str(pokemon.expForNextLevel()))
		self.statsLayout.addRow(self.expLabel, self.expField)

		self.attackLabel = QPushButton("Attack: ")
		self.attackLabel.setEnabled(False)
		self.attackField = QLineEdit()
		self.attackField.setAlignment(Qt.AlignRight)
		self.attackField.setReadOnly(True)
		self.attackField.setText(str(pokemon.attack) + " IV:" + str(pokemon.attackIV) + " EV:" + str(pokemon.attackEV))
		self.statsLayout.addRow(self.attackLabel, self.attackField)

		self.defLabel = QPushButton("Def: ")
		self.defLabel.setEnabled(False)
		self.defField = QLineEdit()
		self.defField.setAlignment(Qt.AlignRight)
		self.defField.setReadOnly(True)
		self.defField.setText(str(pokemon.defense) + " IV:" + str(pokemon.defenseIV) + " EV:" + str(pokemon.defenseEV))
		self.statsLayout.addRow(self.defLabel, self.defField)

		self.specAtkLabel = QPushButton("Spec. Atk: ")
		self.specAtkLabel.setEnabled(False)
		self.specAtkField = QLineEdit()
		self.specAtkField.setAlignment(Qt.AlignRight)
		self.specAtkField.setReadOnly(True)
		self.specAtkField.setText(str(pokemon.specAtk) + " IV:" + str(pokemon.specAtkIV) + " EV:" + str(pokemon.specAtkEV))
		self.statsLayout.addRow(self.specAtkLabel, self.specAtkField)

		self.specDefLabel = QPushButton("Spec. Def: ")
		self.specDefLabel.setEnabled(False)
		self.specDefField = QLineEdit()
		self.specDefField.setAlignment(Qt.AlignRight)
		self.specDefField.setReadOnly(True)
		self.specDefField.setText(str(pokemon.specDef) + " IV:" + str(pokemon.specDefIV) + " EV:" + str(pokemon.specDefEV))
		self.statsLayout.addRow(self.specDefLabel, self.specDefField)

		self.speedLabel = QPushButton("Speed: ")
		self.speedLabel.setEnabled(False)
		self.speedField = QLineEdit()
		self.speedField.setAlignment(Qt.AlignRight)
		self.speedField.setReadOnly(True)
		self.speedField.setText(str(pokemon.speed) + " IV:" + str(pokemon.speedIV) + " EV:" + str(pokemon.speedEV))
		self.statsLayout.addRow(self.speedLabel, self.speedField)

		if self.widget_id >= 0:
			self.slotButtons = []
			for button_index in range(6):
				self.slotButtons.append(QPushButton(str(button_index + 1)))
				self.slotButtons[button_index].setStyleSheet("background-color: #0a64a0; color: #FFFFFF; font-weight: bold; min-width: 45px")
				self.slotButtons[button_index].clicked.connect(partial(self.__slotChange, button_index+1))
				if button_index == self.widget_id:
					self.slotButtons[button_index].setEnabled(False)
				self.slotLayout.addWidget(self.slotButtons[button_index])

			self.slotWidget.setLayout(self.slotLayout)

		self.leftWidget.setLayout(self.leftLayout)
		self.rightWidget.setLayout(self.statsLayout)
		self.mainLayout.addRow(self.leftWidget, self.rightWidget)
		self.mainLayout.addRow(self.slotWidget)
		self.setLayout(self.mainLayout)

	def __slotChange(self, slot):
		self.reorderSignal.emit(self.widget_id, slot)
		self.close()
		