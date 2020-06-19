from PySide2.QtWidgets import QTableWidgetItem
from PySide2.QtCore import Qt

''' QCustomTableWidgetItem

	Custom widget for a table. Allows proepr sorting of numbers.
	Does not treat them as string like the default item does.
'''
class QCustomTableWidgetItem (QTableWidgetItem):
    def __init__ (self, value):
        super(QCustomTableWidgetItem, self).__init__(str('%s' % value))

    def __lt__ (self, other):
        if (isinstance(other, QCustomTableWidgetItem)):
            selfDataValue  = float(self.data(Qt.EditRole).replace(",", ""))
            otherDataValue = float(other.data(Qt.EditRole).replace(",", ""))
            return selfDataValue < otherDataValue
        else:
            return QTableWidgetItem.__lt__(self, other)