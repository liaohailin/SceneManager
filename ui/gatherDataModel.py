""" 
Class derived from QtCore.QAbstractTableModel to display the generic data of an animTransferMap
"""
from Qt import QtCore, QtWidgets, QtCompat, QtGui
from mpc.maya.animationTools.SceneManager.ui.trackedItemDataModel import TrackedItemDataModel

class GatherDataModel(TrackedItemDataModel):
	""" Model class to fill the generic scale view

		Args:
			data (list): list of Tracked ACP
			header (list): list of header string
	"""
	def __init__(self, data, header, parent=None):
		super(GatherDataModel, self).__init__(data, header, parent=parent)

	def headerData(self, col, orientation=QtCore.Qt.Horizontal, role=QtCore.Qt.DisplayRole):
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return ""
		else:
			return super(GatherDataModel, self).trackedItemHeaderData(col, orientation=orientation, role=role)
	
	def data(self, index, role=QtCore.Qt.DisplayRole):
		return super(GatherDataModel, self).trackedItemData(index, role=role)

	def setGatherData(self, index, value):
		""" Changes the value of the data in the table at the specified index
			re-implemented from base class

			Args:
				index(QModelIndex): a row/col index into the QAbstractTableModel
				value(NA): item to be added to the data table
		"""
		if index.isValid():
			gather = value
			trackedItem = self.trackedItem(index)
			asset = self.asset(index)
			if self.isAssetValid(asset):
				trackedItem.setGatherData(asset, gather)
				self.dataChanged.emit(index, index, [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole])

	def flags(self, index):
		if not index.isValid():
			return QtCore.Qt.ItemIsEnabled
		return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

class GatherACPDataModel(GatherDataModel):
	""" Model class to fill the generic scale view

		Args:
			data (list): list of Tracked ACP
			header (list): list of header string
	"""
	def __init__(self, data, header, shotPkg=None, parent=None):
		super(GatherACPDataModel, self).__init__(data, header, parent=parent)
		self._shotPkg = shotPkg

	def inShotPkg(self, index):
		# detect if current acp in current context and in shotPkg
		tracedACP = self.trackedItem(index)
		if tracedACP.trackedItemName in self._shotPkg.acpNameList:
			return True
		else:
			return False

	def resetData(self, data=[], header=[], shotPkg=None):
		# list of tracked items
		self.dataList = data
		self.headerList = header
		self._shotPkg = shotPkg
		#populate row and column
		if self.dataList and self.headerList:
			self.populateData()