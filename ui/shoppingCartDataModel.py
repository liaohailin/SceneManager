""" 
Class derived from QtCore.QAbstractTableModel to display the generic data of an animTransferMap
"""
### start python 3 migration
from builtins import str
from builtins import range
### end python 3 migration
from mpc.maya.animationTools.SceneManager.ui.trackedItemDataModel import TrackedItemDataModel

from Qt import QtCore, QtWidgets, QtCompat, QtGui


class ShoppingCartDataModel(TrackedItemDataModel):
	""" Model class to fill the generic scale view

		Args:
			data (list): list of Tracked ACP
			header (list): list of header string
	"""
	itemAdded = QtCore.Signal()

	def __init__(self, data, header, parent=None):
		super(ShoppingCartDataModel, self).__init__(data=data, header=header, parent=parent)
		# tracked items
		self.removeItem(self.dataList[0])

	def data(self, index, role):
		""" Returns the data to be displayed at the index
			re-implemented from base class

			Args:
				index(QModelIndex): a row/col index into the QAbstractTableModel
				role(int): Qt flag (should be QtCore.Qt.DisplayRole for display)
			
			Returns:
				The data stored in the row/column supplied by the index
		"""
		if index.isValid() and role == QtCore.Qt.DisplayRole:
			trackedItem = self.trackedItem(index)
			if self.headerData(index.column()) == "Name":
				return trackedItem.trackedItemName
			elif self.headerData(index.column()) == "Shot":
				if trackedItem.packageAsset.tessaAsset:
					return trackedItem.packageAsset.tessaAsset.context.shot.name
				else:
					return "None"

	def headerData(self, col, orientation=QtCore.Qt.Horizontal, role=QtCore.Qt.DisplayRole):
		""" Returns the header for the column
			re-implemented from base class

			Args:
				col(int): index of the column whose header you want
				orientation(Qt.Orientation): column orientation (horizontal/vertical)
				role(int): Qt flag (should be QtCore.Qt.DisplayRole for display)
		"""
		#super(ShoppingCartDataModel, self).headerData(col, orientation, role)
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return self.headerList[col]

	def getGatherAssets(self, index):
		trackedItem = self.trackedItem(index)
		gatherAssets = []
		for assetAttr in trackedItem.interactiveAssetAttrs:
			asset = trackedItem.getAsset(assetAttr)
			if asset and asset.ifGather:
				gatherAssets.append(asset)
		return gatherAssets
	
	def updateItem(self, trackedItem):
		# update shopping cart model
		if trackedItem.updateList:
			if trackedItem not in self.dataList:
				rowData = []
				for column in range(self.columnCount()):
					rowData.append(QtGui.QStandardItem(column))
				self.appendRow(rowData)
				self.dataList.append(trackedItem)
			firstIndex = self.index(self.dataList.index(trackedItem), 0)
			self.dataChanged.emit(firstIndex, firstIndex, [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole])
		else:
			self.removeItem(trackedItem)
		self.itemAdded.emit()

	def removeItem(self, item):
		if item not in self.dataList:
			return
		row = self.dataList.index(item)
		self.takeRow(row)
		self.dataList.remove(item)
	
	def flags(self, index):
		if not index.isValid():
			return QtCore.Qt.ItemIsEnabled
		return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled