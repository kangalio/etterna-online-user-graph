import json, os
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pyqtgraph as pg

from calculate import generate_ratings_file

class UI(QApplication):
	root = None
	plot = None
	inputbox = None
	
	callbacks = None # State object, used for its callback functions
	
	def __init__(self, usernames, callbacks):
		super().__init__(["EtternaOnline user graph visualizer"])
		
		self.callbacks = callbacks
		
		root = QWidget()
		self.root = root
		layout = QVBoxLayout(root)
		self.layout = layout
		
		inputbox = QLineEdit()
		self.inputbox = inputbox
		inputbox.returnPressed.connect(lambda: self.inputbox_callback())
		
		completer = QCompleter(usernames)
		completer.setCaseSensitivity(Qt.CaseInsensitive)
		completer.setCompletionMode(QCompleter.InlineCompletion)
		inputbox.setCompleter(completer)
		
		button_row_widget = QWidget()
		button_row = QHBoxLayout(button_row_widget)
		layout.addWidget(button_row_widget)
		layout.addWidget(inputbox)
		
		button = QPushButton("Add closest player by skill level")
		button.setToolTip("Click multiple times to add more users with close skill levels")
		button.clicked.connect(self.callbacks.add_close_player)
		button_row.addWidget(button)
		
		button = QPushButton("Add top player")
		button.setToolTip("You can click multiple times to add more top players")
		button.clicked.connect(self.callbacks.add_top_player)
		button_row.addWidget(button)
		
		plot_widget = pg.PlotWidget()
		self.plot = plot_widget.getPlotItem()
		self.plot.addLegend()
		layout.addWidget(plot_widget)
		
		root.show()
	
	def inputbox_callback(self):
		text = self.inputbox.text()
		self.inputbox.clear()
		
		for name in text.split(): # Split input on whitespace
			self.callbacks.add_user(self.callbacks.find_user(name))

class State:
	items = []
	plotted_users = []
	
	users, ui = None, None
	this_user = None
	
	def __init__(self):
		self.users = json.load(open("ratings.json"))
		#self.users = json.load(open("ratings-aaaa.json"))
		
		self.this_user = self.find_user("kangalioo") # REMEMBER
		
		usernames = [user["username"] for user in self.users]
		self.ui = UI(usernames, self) # Pass self as callback holder
	
	def run(self):
		self.ui.exec_()
	
	def find_user(self, name):
		for user in self.users:
			if user["username"].lower() == name.lower(): return user
		return None
	
	def add_user(self, user):
		x, y = user["years"], user["ratings"]
		pen = (1, 1)
		item = self.ui.plot.plot(x, y, pen=pen, antialias=True)
		self.items.append(item)
		self.plotted_users.append(user)
		
		self.ui.plot.legend.addItem(item, user["username"])
		
		for (i, item) in enumerate(self.items):
			pen = (i, len(self.items))
			item.setPen(pen)
	
	# Plots the highest player (ranked by `sorting_key`) that's not
	# already plotted. If `top_first` is False, the lowest player is
	# chosen.
	# TODO: this is pretty horible efficiency-wise (sorting the whole
	# list just to get one element). Maybe improve?
	def add_first_by(self, sorting_key, top_first=True):
		users = sorted(self.users, key=sorting_key, reverse=top_first)
		for user in users:
			if not user in self.plotted_users:
				self.add_user(user)
				break
	
	def add_top_player(self):
		self.add_first_by(lambda user: user["ratings"][-1])
	
	def add_close_player(self):
		def map_rating_delta(user):
			my_rating = self.this_user["ratings"][-1]
			other_rating = user["ratings"][-1]
			return abs(my_rating - other_rating)
		
		self.add_first_by(map_rating_delta, top_first=False)

#generate_ratings_file()
State().run()
