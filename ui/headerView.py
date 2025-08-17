### start python 3 migration
from __future__ import division
### end python 3 migration

from Qt import QtCore, QtWidgets, QtGui
from mpc.pyPaths import mpcSharedResourcePath

from mpc.maya.animationTools.SceneManager.ui import qtUtils


class IconHeaderView(QtWidgets.QHeaderView):

	def __init__(self, activeColor=None, parent=None):
		"""
		"""
		super(IconHeaderView, self).__init__(QtCore.Qt.Horizontal, parent)
		self.iconSize = 30
		if activeColor:
			self.activeIconColor = activeColor
		else:
			self.activeIconColor = QtGui.QColor("#8AD1CC")
		self.setMinimumHeight(self.iconSize)# only affect height of header bar itself
		self.setDefaultSectionSize(60)
		self.setSectionsClickable(True)

	def event(self, event):
		if event.type() == QtCore.QEvent.ToolTip:
			index = self.logicalIndexAt(event.pos())
			tooltip = self.model().trackedItemHeaderData(
				index,
				QtCore.Qt.Horizontal,
				QtCore.Qt.UserRole
			)
			QtWidgets.QToolTip.showText(event.globalPos(), "select column-{0}".format(tooltip), self)
			return True
		return super(IconHeaderView, self).event(event)

	def paintSection(self, painter, rect, index):
		""" Overridden from the class to allow us
			to give custom style to the child columns
			when they are expanded.
			Args:
				painter (QPainter): The painter being used to paint the headers
				rect (QRect): The rectangle representing the header
				index (int): The index of the column to paint
		"""
		painter.save()
		super(IconHeaderView, self).paintSection(painter, rect, index)
		painter.restore()

		if self.model().rowCount()==0:
			return
		iconPath = self.model().trackedItemHeaderData(
			index,
			QtCore.Qt.Horizontal,
			QtCore.Qt.DecorationRole
		)
		assetDisplayText = self.model().trackedItemHeaderData(
			index,
			QtCore.Qt.Horizontal,
			QtCore.Qt.DisplayRole
		)
		if index!=0:
			#painter.fillRect(rect, self.palette().window())
			# Draw the icon
			headerIconTargetRect = QtCore.QRect(rect.x()+rect.width()/2-self.iconSize/2, rect.y(), self.iconSize, self.iconSize)
			headerIconTargetRect = qtUtils.addPaddingToRect(headerIconTargetRect, 5)
			if self.model().columnAssetValid(index):
				coloredPixmap = qtUtils.getColoredPixmap(iconPath, self.activeIconColor, headerIconTargetRect.width(), headerIconTargetRect.height())
			else:
				coloredPixmap = qtUtils.getColoredPixmap(iconPath, QtGui.QColor("#7B7D7D"), headerIconTargetRect.width(), headerIconTargetRect.height())
			painter.drawPixmap(headerIconTargetRect, coloredPixmap)
		else:
			painter.drawText(rect, QtCore.Qt.AlignCenter, assetDisplayText)