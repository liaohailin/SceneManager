### start python 3 migration
from builtins import str
from builtins import range
### end python 3 migration

from Qt import QtCore, QtWidgets, QtCompat, QtGui
from mpc.pyPaths import mpcSharedResourcePath


class TrackedItemDataModel(QtGui.QStandardItemModel):
	""" Model class to fill the generic scale view

		Args:
			data (list): list of Tracked ACP
			header (list): list of header string
	"""
	def __init__(self, data, header, parent=None):
		super(TrackedItemDataModel, self).__init__(parent=parent)
		# list of tracked items
		self.dataList = data
		self.headerList = header
		#populate row and column
		if self.dataList and self.headerList:
			self.populateData()

	def trackedItem(self, index):
		return self.dataList[index.row()]

	def setTrackedItem(self, index, item):
		self.dataList[index.row()] = item

	def asset(self, index):
		trackedItem = self.trackedItem(index)
		assetAttr = self.assetAttr(index)
		return trackedItem.getAsset(assetAttr)

	def assetAttr(self, index):
		if isinstance(index, int):
			return self.headerList[index]
		elif isinstance(index, QtCore.QModelIndex):
			return self.headerList[index.column()]

	def columnCount(self, parent=None):
		return len(self.headerList)
	
	def rowCount(self, parent=None):
		return len(self.dataList)

	def populateData(self):
		self.clear()
		for row in range(len(self.dataList)):
			for column in range(len(self.headerList)):
				item = QtGui.QStandardItem("{0}-{1}".format(row, column))
				self.setItem(row, column, item)

	def resetData(self, data=[], header=[]):
		# list of tracked items
		self.dataList = data
		self.headerList = header
		#populate row and column
		if self.dataList and self.headerList:
			self.populateData()

	#-------validation-------
	def isAssetValid(self, asset):
		if asset and asset.tessaAsset:
			return True
		else:
			return False
	
	def columnAssetValid(self, column):
		for row in range(self.rowCount()):
			asset = self.asset(self.index(row, column))
			if self.isAssetValid(asset):
				return True
		return False

	#------header data-----
	def trackedItemHeaderData(self, col, orientation=QtCore.Qt.Horizontal, role=QtCore.Qt.DisplayRole):
		if self.rowCount()==0:
			return ""
		firstItemAsset = self.asset(self.index(0, col))
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return firstItemAsset.display
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.UserRole:
			return firstItemAsset.toolTip
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DecorationRole:
			if getattr(firstItemAsset, "iconFile", None):
				return mpcSharedResourcePath(u"animationTools", u"!RESOURCE_INSTALL_PATH!", u"img/sceneManager/" + firstItemAsset.iconFile)
			else:
				return mpcSharedResourcePath(u"animationTools", u"!RESOURCE_INSTALL_PATH!", u"img/sceneManager/" + "SM_icon_help.svg")
	
	#------data-------
	def trackedItemData(self, index, role=QtCore.Qt.DisplayRole):
		if index.isValid() and role == QtCore.Qt.DisplayRole:
			trackedItem = self.trackedItem(index)
			asset = self.asset(index)
			if index.column() ==0:
				return trackedItem.trackedItemName
			else:
				if self.isAssetValid(asset):
					return str(asset.tessaAsset.version)
				else:
					return "N/A"