from PySide2.QtWidgets import QFrame

class HorizontalLineWidget(QFrame):

	def __init__(self, height=20):
		super(HorizontalLineWidget, self).__init__()
		self.setFrameShape(QFrame.HLine)
		self.setFrameShadow(QFrame.Sunken)
		self.setFixedHeight(height)