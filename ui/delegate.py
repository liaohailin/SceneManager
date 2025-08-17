### start python 3 migration
from __future__ import division
from builtins import str
from builtins import range
### end python 3 migration

from Qt import QtCore, QtWidgets, QtGui
from mpc.pyPaths import mpcSharedResourcePath

from mpc.maya.animationTools.SceneManager.ui import qtUtils
from mpc.maya.animationTools.SceneManager.ui.customWidgets import CustomComboBox
from mpc.maya.animationTools.SceneManager.core.trackedItem import (trackedAudio, trackedCameraPkg)

class GatherDelegate(QtWidgets.QStyledItemDelegate):
	""" A delegate that places a fully functioning QComboBox in every
		cell of the column to which it's applied
	"""
	def __init__(self, view, model, shoppingCartModel, activeColor=None, parent=None):
		""" Constructor.

			Args:
				parent(QObject): of a parent widget.

			Kwargs:
				root(object): of a parent class object
				context(context): of a current context.
		"""
		super(GatherDelegate, self).__init__(parent)
		self.view = view
		self.model = model
		self.shoppingCartModel = shoppingCartModel
		self.padding = 10
		if activeColor:
			self.activeIconColor = activeColor
		else:
			self.activeIconColor = QtGui.QColor("#8AD1CC")
		self.view.horizontalHeader().sectionClicked.connect(self.onHeaderClicked)

	def onHeaderClicked(self, col):
		# set selected version to latest
		if col != 0:
			selectedIndexes = self.view.selectionModel().selectedRows(column=col)
			if not selectedIndexes:
				selectedIndexes = [self.model.index(row, col) for row in range(self.model.rowCount())]

			for index in selectedIndexes:
				pushButton = self.view.indexWidget(index)
				if pushButton:
					pushButton.setChecked(not pushButton.isChecked())

	def createIndexPB(self, index):
		gatherButton = QtWidgets.QPushButton(self.view)
		iconPath = self.model.headerData(
			index.column(),
			QtCore.Qt.Horizontal,
			QtCore.Qt.DecorationRole
		)
		coloredPixmap = qtUtils.getColoredPixmap(iconPath, QtGui.QColor("#7B7D7D"))
		gatherButton.setIcon(QtGui.QIcon(coloredPixmap))
		#gatherButton.setFixedSize(QtCore.QSize(option.rect.width()-self.padding, option.rect.height()-self.padding))
		gatherButton.setCheckable(True)
		gatherButton.toggled.connect(lambda: self._updateModel(index, gatherButton))
		gatherButton.toggled.connect(lambda: self._updateIconColor(index))
		return gatherButton

	def paint(self, painter, option, index): #pylint: disable=unused-argument
		""" The delegate using the given painter and style option for the item specified by index

			Args:
				painter(QtGui.QPainter): The painter to draw a checkBox shape.
				option(QStyleOptionViewItem): The option used for rendering the item
				index(QModelIndex): The index being edited
		"""
		if index.column() != 0:
			# paint header
			# paint other part
			if not self.view.indexWidget(index):
				gatherButton = self.createIndexPB(index)
				self.view.setIndexWidget(index, gatherButton)
			gatherButton = self.view.indexWidget(index)
			gatherButton.setToolTip(self.model.data(index, QtCore.Qt.DisplayRole))
			gatherButton.setChecked(self.model.asset(index).ifGather)
			# change button status according to current text
			if gatherButton.toolTip()=="N/A":
				gatherButton.setEnabled(False)
		super(GatherDelegate, self).paint(painter, option, index)
		# resize text
		text = self.model.trackedItemData(index, QtCore.Qt.DisplayRole)
		font_metrics = QtGui.QFontMetrics(painter.font())
		text_width = font_metrics.width(text)+10
		if text_width>option.rect.width():
			self.view.setColumnWidth(index.column(), text_width)

	def _updateIconColor(self, index):
		gatherButton = self.view.indexWidget(index)
		iconPath = self.model.headerData(
					index.column(),
					QtCore.Qt.Horizontal,
					QtCore.Qt.DecorationRole
				)
		if gatherButton.isChecked() and gatherButton.isEnabled():
			coloredPixmap = qtUtils.getColoredPixmap(iconPath, self.activeIconColor)
		else:
			coloredPixmap = qtUtils.getColoredPixmap(iconPath, QtGui.QColor("#7B7D7D"))
		gatherButton.setIcon(QtGui.QIcon(coloredPixmap))

	def updateEditorGeometry(self, editor, option, index): #pylint: disable=unused-argument
		""" Ensures that the editor is displayed correctly with respect to the item view.

			Args:
				editor(QPushButton): The editor to set new value.
				option(QStyleOptionViewItem): The option used for rendering the item
				index(QModelIndex): The index being edited.
		"""
		editor.setGeometry(option.rect)

	def _updateModel(self, index, editor):
		self.model.setGatherData(index, editor.isChecked())
		trackedItem = self.model.trackedItem(index)
		self.shoppingCartModel.updateItem(trackedItem)

class ACPGatherDelegate(GatherDelegate):
	""" A delegate that places a fully functioning QComboBox in every
		cell of the column to which it's applied
	"""
	def __init__(self, view, model, shoppingCartModel, parent=None):
		""" Constructor.

			Args:
				parent(QObject): of a parent widget.

			Kwargs:
				root(object): of a parent class object
				context(context): of a current context.
		"""
		super(ACPGatherDelegate, self).__init__(view, model, shoppingCartModel, parent)

	def createIndexPB(self, index):
		gatherButton = super(ACPGatherDelegate, self).createIndexPB(index)
		gatherButton.toggled.connect(lambda: self._updateNeighborButton(index))
		return gatherButton
	
	def paint(self, painter, option, index): #pylint: disable=unused-argument
		""" The delegate using the given painter and style option for the item specified by index

			Args:
				painter(QtGui.QPainter): The painter to draw a checkBox shape.
				option(QStyleOptionViewItem): The option used for rendering the item
				index(QModelIndex): The index being edited
		"""
		if index.column() == 0:
			if not self.model.inShotPkg(index):
				#draw pink to show asset not in shotPkg
				#draw a gradient color through the whole row
				startColor = QtGui.QColor("#E470AB")
				endColor = QtGui.QColor("#414042")
				# Create a linear gradient
				gradient = QtGui.QLinearGradient(option.rect.topLeft(), option.rect.topRight())
				gradient.setColorAt(0, startColor)
				gradient.setColorAt(1, endColor)
				# Save the painter's current state
				painter.save()
				# Draw the gradient background
				painter.fillRect(option.rect, gradient)
				# Restore the painter's state
				painter.restore()
		super(ACPGatherDelegate, self).paint(painter, option, index)

	def _updateNeighborButton(self, index):
		gatherButton = self.view.indexWidget(index)
		nextValue = 0
		if index.column()==1 or index.column()==3:
			nextValue = 1
		elif index.column()==2 or index.column()==4:
			nextValue = -1
		else:
			return
		nextIndex = self.model.index(index.row(), index.column()+nextValue)
		nextButton = self.view.indexWidget(nextIndex)
		if nextButton and gatherButton.isChecked():
			nextButton.setChecked(False)
		animCurveColumn = 0
		if index.column()==1 or index.column()==2:
			animCurveColumn = 5
		elif index.column()==3 or index.column()==4:
			animCurveColumn = 6

		animCurveIndex = self.model.index(index.row(), animCurveColumn)
		animCurveButton = self.view.indexWidget(animCurveIndex)
		if animCurveButton:
			if gatherButton.isChecked() or nextButton.isChecked():
				animCurveButton.setChecked(True)
			else:
				animCurveButton.setChecked(False)

	def _updateModel(self, index, editor):
		currentPB = editor
		if index.column()==5:
			highBodyPB = self.view.indexWidget(self.model.index(index.row(), 1))
			lowBodyPB = self.view.indexWidget(self.model.index(index.row(), 2))
			if not highBodyPB.isChecked() and not lowBodyPB.isChecked() and currentPB.isChecked():
				return
		elif index.column()==6:
			highFacePB = self.view.indexWidget(self.model.index(index.row(), 3))
			lowFacePB = self.view.indexWidget(self.model.index(index.row(), 4))
			if not highFacePB.isChecked() and not lowFacePB.isChecked() and currentPB.isChecked():
				return
		super(ACPGatherDelegate, self)._updateModel(index, currentPB)


class CameraGatherDelegate(GatherDelegate):
	""" A delegate that places a fully functioning QComboBox in every
		cell of the column to which it's applied
	"""
	def __init__(self, view, model, shoppingCartModel, activeColor=None, parent=None):
		""" Constructor.

			Args:
				parent(QObject): of a parent widget.

			Kwargs:
				root(object): of a parent class object
				context(context): of a current context.
		"""
		super(CameraGatherDelegate, self).__init__(view, model, shoppingCartModel, activeColor, parent)

	def createIndexPB(self, index):
		gatherButton = super(CameraGatherDelegate, self).createIndexPB(index)
		if index.column() == 1:
			# if it's button of cameraRig, register extra button logic
			gatherButton.toggled.connect(lambda: self._updateNeighborButton(index))
		else:
			gatherButton.setEnabled(False)
		return gatherButton
		
	def _updateNeighborButton(self, index):
		cameraRigButton = self.view.indexWidget(index)

		for restButtonCol in range(index.column() + 1, self.model.columnCount()):
			restButtonIndex = self.model.index(index.row(), restButtonCol)
			restButton = self.view.indexWidget(restButtonIndex)
			restButton.setEnabled(cameraRigButton.isChecked())
			restButton.setChecked(cameraRigButton.isChecked())


class CartDelegate(QtWidgets.QStyledItemDelegate):
	""" A delegate that places a fully functioning QComboBox in every
		cell of the column to which it's applied
	"""
	def __init__(self, view, model, parent=None):
		""" Constructor.

			Args:
				parent(QObject): of a parent widget.

			Kwargs:
				root(object): of a parent class object
				context(context): of a current context.
		"""
		super(CartDelegate, self).__init__(parent)
		self.view = view
		self.model = model
		self.pixmapSize = 15
		self.padding = 10

	def paint(self, painter, option, index): #pylint: disable=unused-argument
		""" The delegate using the given painter and style option for the item specified by index

			Args:
				painter(QtGui.QPainter): The painter to draw a checkBox shape.
				option(QStyleOptionViewItem): The option used for rendering the item
				index(QModelIndex): The index being edited
		"""
		originRect = QtCore.QRect(option.rect.x(), option.rect.y(), option.rect.width(), option.rect.height())
		# Save the current state of the painter
		painter.save()
		# Draw the item inside the padded rect
		option.rect = option.rect.adjusted(0, 0, 0, -self.padding)
		super(CartDelegate, self).paint(painter, option, index)

		# Restore the painter's state
		painter.restore()

		painter.save()
		if self.model.headerData(index.column()) == "Name":
			offset = 0
			trackedItem = self.model.trackedItem(index)
			if isinstance(trackedItem, trackedCameraPkg.TrackedCameraPkg):
				iconColor = "#C5DA83"
			elif isinstance(trackedItem, trackedAudio.TrackedAudio):
				iconColor = "#F3CE5E"
			else:# acp or other undefined types
				iconColor = "#8AD1CC"
			for asset in self.model.getGatherAssets(index):
				pixmapRect = QtCore.QRect(originRect.x()+self.pixmapSize/2+offset, originRect.y()+originRect.height()-self.pixmapSize, self.pixmapSize, self.pixmapSize)
				iconPath = mpcSharedResourcePath(u"animationTools", u"!RESOURCE_INSTALL_PATH!", u"img/sceneManager/" + asset.iconFile)
				coloredPixmap = qtUtils.getColoredPixmap(iconPath, QtGui.QColor(iconColor), pixmapRect.width(), pixmapRect.height())
				painter.drawPixmap(pixmapRect, coloredPixmap)
				offset += self.pixmapSize
		painter.restore()

	def updateEditorGeometry(self, editor, option, index): #pylint: disable=unused-argument
		""" Ensures that the editor is displayed correctly with respect to the item view.

			Args:
				editor(QPushButton): The editor to set new value.
				option(QStyleOptionViewItem): The option used for rendering the item
				index(QModelIndex): The index being edited.
		"""
		editor.setGeometry(option.rect)

class UpdateDelegate(QtWidgets.QStyledItemDelegate):
	""" A subclass of QStyledItemDelegate that allows us to render our
		pretty star ratings.
	"""
	def __init__(self, view, model, parent=None):
		super(UpdateDelegate, self).__init__(parent)
		self.view = view
		self.model = model
		self.comboBoxSize = QtCore.QSize(40, 30)
		self.view.horizontalHeader().sectionClicked.connect(self.onHeaderClicked)

	def createEditor(self, parent, option, index):
		if index.column() == 0:
			return
		comboBox = CustomComboBox(parent)
		asset = self.model.asset(index)
		if asset:
			for version, published in asset.assetVersions.items():
				comboBox.addItem(str(version))
				if published:
					comboBox.setItemData(comboBox.count() - 1, QtGui.QColor("#1BFB00"), role=QtCore.Qt.ForegroundRole)
			comboBox.addItem("N/A")
			# close the editor after a value is selected or if clicked outside the editor
			comboBox.activated.connect(lambda index: self.editorIndexChanged(comboBox))
		return comboBox

	def editorIndexChanged(self, comboBox):
		self.view.commitData(comboBox)
		self.view.closeEditor(comboBox, self.NoHint)

	def setEditorData(self, editor, index):
		# show the editor's popup on a single click
		editor.showPopup()
		# set the current cell data onto the editor
		value = self.model.trackedItemData(index)
		value = value.split("v")[-1]
		if value:
			i = editor.findText(value)
			if i == -1:
				i = 0
			editor.setCurrentIndex(i)

	def setModelData(self, editor, model, index):
		model.setData(index, editor.currentText(), QtCore.Qt.EditRole)

	def onHeaderClicked(self, col):
		# set selected version to latest
		if col!=0:
			selectedIndexes = self.view.selectionModel().selectedRows(column=col)
			if not selectedIndexes:
				selectedIndexes = [self.model.index(row, col) for row in range(self.model.rowCount())]
			for index in selectedIndexes:
				data = ""
				asset = self.model.asset(index)
				if self.model.isAssetValid(asset):
					data = str(list(asset.assetVersions)[0])
				else:
					data = "N/A"
				self.model.setData(index, data, QtCore.Qt.EditRole)

	def paint(self, painter, option, index): #pylint: disable=unused-argument
		""" The delegate using the given painter and style option for the item specified by index

			Args:
				painter(QtGui.QPainter): The painter to draw a checkBox shape.
				option(QStyleOptionViewItem): The option used for rendering the item
				index(QModelIndex): The index being edited
		"""
		if index.column() == 0 and not self.model.inShotPkg(index):
			# Get the rectangle for the row
			rowRect = QtCore.QRect(option.rect.x(), option.rect.y(), option.rect.width(), option.rect.height())
			# Calculate the row rectangle covering all columns
			lastRect = self.view.visualRect(self.model.index(index.row(), self.model.columnCount()-1))
			rowRect.setRight(lastRect.right())	
			#draw pink to show asset not in shotPkg
			color = "#E470AB"
			#draw a gradient color through the whole row
			startColor = QtGui.QColor("#E470AB")
			endColor = QtGui.QColor("#414042")
			# Create a linear gradient
			gradient = QtGui.QLinearGradient(rowRect.topLeft(), rowRect.topRight())
			gradient.setColorAt(0, startColor)
			gradient.setColorAt(1, endColor)
			# Save the painter's current state
			painter.save()
			# Draw the gradient background
			painter.fillRect(rowRect, gradient)
			# Restore the painter's state
			painter.restore()
		# Call the base class's paint method to draw the item
		painter.save()
		super(UpdateDelegate, self).paint(painter, option, index)
		painter.restore()
		# Draw Text on top of everything
		color = ""
		# set rect color depend on the status of asset
		asset = self.model.asset(index)
		if asset:
			if asset.ifUpdate or asset.ifGather or asset.ifRemove:
				color = "blue"
			elif index.column()==0:
				if asset.hubPrefix != asset.newHubPrefix:
					color = "blue"
				else:
					color = "white"
			elif self.model.trackedItemData(index) == "N/A":
				color = "white"
			elif self.model.assetOutDated(asset):
				color = "#EF4A3E"
			else:
				color = "#C5DA83"
		else:
			color = "white"
		painter.save()
		# Set the text color
		painter.setPen(QtGui.QColor(color))
		# Draw the text explicitly
		text = self.model.trackedItemData(index, QtCore.Qt.DisplayRole)
		if text:
			if index.column()==0:
				painter.drawText(option.rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, text)
			else:
				painter.drawText(option.rect, QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter, text)
		# Restore the painter's state
		painter.restore()
		font_metrics = QtGui.QFontMetrics(painter.font())
		text_width = font_metrics.width(text)+10
		if text_width>option.rect.width():
			self.view.setColumnWidth(index.column(), text_width)

		#make sure the view is updated properly
		self.view.update()

	def updateEditorGeometry(self, editor, option, index): #pylint: disable=unused-argument
		""" Ensures that the editor is displayed correctly with respect to the item view.

			Args:
				editor(QPushButton): The editor to set new value.
				option(QStyleOptionViewItem): The option used for rendering the item
				index(QModelIndex): The index being edited.
		"""
		editor.setGeometry(option.rect)