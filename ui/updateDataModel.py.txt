""" 
Class derived from QtCore.QAbstractTableModel to display the generic data of an animTransferMap
"""
### start python 3 migration
from builtins import str
from builtins import range
### end python 3 migration

import re
from Qt import QtCore, QtWidgets, QtCompat, QtGui

from mpc.maya.animationTools.SceneManager.ui.trackedItemDataModel import TrackedItemDataModel

class UpdateDataModel(TrackedItemDataModel):
	""" Model class to fill the generic scale view

		Args:
			data (list): list of Tracked ACP
			header (list): list of header string
	"""
	userEdited = QtCore.Signal(object)
	def __init__(self, data, header, shotPkg=None, parent=None):
		super(UpdateDataModel, self).__init__(data, header, parent=parent)
		self.dataRemoveList = []
		self._shotPkg = shotPkg

	#----------data validation--------------
	def inShotPkg(self, index):
		return True

	def isAssetValid(self, asset):
		"""Returns True if the current audio is in the scene and is not about to removed
		OR
		Returns True if the audio is not in the scene but is about to be gathered
		"""
		return (asset.inScene() and not asset.ifRemove) or (not asset.inScene() and asset.ifGather)

	def assetOutDated(self, asset):
		#TODO: this should be moved elsewhere since it's not making use of 'self'
		return list(asset.assetVersions)[0] > asset.currentVersion

	#------------model override functions----------------
	def headerData(self, col, orientation=QtCore.Qt.Horizontal, role=QtCore.Qt.DisplayRole):
		""" Returns the header for the column
			re-implemented from base class

			Args:
				col(int): index of the column whose header you want
				orientation(Qt.Orientation): column orientation (horizontal/vertical)
				role(int): Qt flag (should be QtCore.Qt.DisplayRole for display)
		"""
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return ""

	def data(self, index, role=QtCore.Qt.DisplayRole):
		""" Returns the data to be displayed at the index
			re-implemented from base class to return empty string because we would set the cell data explicitly

			Args:
				index(QModelIndex): a row/col index into the QAbstractTableModel
				role(int): Qt flag (should be QtCore.Qt.DisplayRole for display)
			
			Returns:
				empty string
		"""
		if role == QtCore.Qt.DisplayRole:
			return ""

	#------------api functions----------------
	def resetData(self, data=[], header=[], shotPkg=None):
		"""Updates the current model data with the new 'data'
		"""
		super(UpdateDataModel, self).resetData(data=data, header=header)
		del self.dataRemoveList[:]
		self._shotPkg = shotPkg

	def removeItem(self, index):
		trackedItem = self.trackedItem(index)
		for assetAttr in trackedItem.interactiveAssetAttrs:
			asset = trackedItem.getAsset(assetAttr)
			asset.ifRemove = True
			asset.ifGather = False
			asset.ifUpdate = False
			if asset not in trackedItem.updateList:
				trackedItem.updateList.append(asset)
		self.takeRow(index.row())
		self.dataRemoveList.append(trackedItem)
		self.dataList.remove(trackedItem)
		self.userEdited.emit(index)

	def setUpdateData(self, index, value):
		# no need to update version if the new value is the same as in the scene
		asset = self.asset(index)
		if self.asset(index).sceneVersion == value:
			versionWasChangedButNotCommitted = False
			if asset.ifGather:
				asset.ifGather = False
				versionWasChangedButNotCommitted = True
			if asset.ifUpdate:
				asset.ifUpdate = False
				versionWasChangedButNotCommitted = True
			# if the version was changed in comboBox but was not applied, just change the display color, restore the tessa asset and return
			if versionWasChangedButNotCommitted:
				asset.changeVersion(int(value))
				self.dataChanged.emit(index, index, [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole])
				return
		# set update data only when the value has changed
		if value == self.trackedItemData(index).split("v")[-1]:	
			return
		# change the version to be commited later with the Apply button
		trackedItem = self.trackedItem(index)
		if not asset.inScene():
			asset.ifGather = True
			asset.ifUpdate = False
			asset.ifRemove = False
		else:
			asset.ifUpdate = True
			asset.ifGather = False
			asset.ifRemove = False
		asset.changeVersion(int(value))
		if asset not in trackedItem.updateList:
			trackedItem.updateList.append(asset)
		self.dataChanged.emit(index, index, [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole])
		self.userEdited.emit(index)

	def setRemoveData(self, index):
		trackedItem = self.trackedItem(index)
		asset = self.asset(index)
		asset.ifRemove = True
		asset.ifGather = False
		asset.ifUpdate = False
		if asset not in trackedItem.updateList:
			trackedItem.updateList.append(asset)
		self.dataChanged.emit(index, index, [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole])
		self.userEdited.emit(index)

	def flags(self, index):
		if not index.isValid():
			return QtCore.Qt.ItemIsEnabled
		return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable


class UpdateACPDataModel(UpdateDataModel):
	""" Update ACP data model
	"""
	def __init__(self, data, header, shotPkg=None, parent=None):
		super(UpdateACPDataModel, self).__init__(data, header, shotPkg=shotPkg, parent=parent)

	#----------data validation--------------
	def inShotPkg(self, index):
		# detect if current acp in current context and in shotPkg
		tracedACP = self.trackedItem(index)
		if tracedACP.trackedItemName in self._shotPkg.acpNameList:
			return True
		else:
			return False

	#------------model override functions----------------
	def setData(self, index, value, role):
		if not index.isValid() or role != QtCore.Qt.EditRole:
			return False
		# if value didn't change no need to set data
		if value==self.trackedItemData(index):
			return False
		# anim curve updates
		if index.column()==5 or index.column()==6:
			if value != "N/A":
				self.setUpdateData(index, value)
			else:
				self.setRemoveData(index)
		# rig updates
		elif index.column()>0 and index.column()<5:
			nextValue = 0
			if index.column()==1 or index.column()==3:
				nextValue = 1
			elif index.column()==2 or index.column()==4:
				nextValue = -1
			if value!="N/A":
				nextIndex = self.index(index.row(), index.column()+nextValue)
				if self.trackedItemData(nextIndex) != "N/A":
					self.setRemoveData(nextIndex)
				self.setUpdateData(index, value)
			else:
				self.setRemoveData(index)
		return True

	#------------api functions----------------
	def getPromotableACPs(self, index):
		""" decide if current tracked item is promotable
		arg: targetACP(tessaAsset)
		1. rigpuppet needs to be the same as the target item
		2. if acp already in scene can't promote
		"""
		currentACP = self.trackedItem(index)
		# 1. get same rigpuppet acp
		potentialTargets = []
		for acp in self._shotPkg.acpList:
			if re.match("[a-z0-9A-Z]*[A-Z]v", acp.name):
				potentialTargets.append(acp)
		resultTargetACPs = []
		for targetACP in potentialTargets:
			for assetAttr in currentACP.rigPuppetAttrs:
				rigPuppetAsset = currentACP.getAsset(assetAttr)
				if (not rigPuppetAsset) or (not rigPuppetAsset.tessaAsset):
					continue
				targetRig = rigPuppetAsset.getAssetFromPackage(targetACP)
				if not targetRig:
					continue
				if rigPuppetAsset.tessaAsset.getAsset()==targetRig.getAsset():
					resultTargetACPs.append(targetACP)
		# 2. get acp that's not in scene already
		promotableACPs = []
		trackedItemNameList = [trackedItem.trackedItemName for trackedItem in self.dataList]
		for targetACP in set(resultTargetACPs):
			if targetACP.name not in trackedItemNameList:
				promotableACPs.append(targetACP)
		return promotableACPs

	def promoteItem(self, index, targetACP):
		# translate: change index acp name to targetACP name
		currentACP = self.trackedItem(index)
		currentACP.promote(targetACP)
		if currentACP.packageAsset not in currentACP.updateList:
			currentACP.updateList.append(currentACP.packageAsset)
		self.userEdited.emit(index)


class UpdateAudioDataModel(UpdateDataModel):
	""" A data model class for the audio items on the Manage tab of the UI
	"""

	def inShotPkg(self, index):
		"""Returns True if the current audio is in the corresponding shotPkg
		"""
		trackedAudio = self.trackedItem(index)
		if self._shotPkg.audioAsset:
			return trackedAudio.trackedItemName == self._shotPkg.audioAsset.name
		return False

	#------------model override functions----------------
	def setData(self, index, value, role):
		"""Sets editor data in the cell whether to remove or update the current audio
		"""
		if not index.isValid() or role != QtCore.Qt.EditRole:
			return False
		# if value didn't change no need to set data
		if value==self.trackedItemData(index):
			return False
		if index.column() > 0:
			if value != "N/A":
				self.setUpdateData(index, value)
			else:
				self.setRemoveData(index)
		return True

class UpdateCameraDataModel(UpdateDataModel):

	def inShotPkg(self, index):
		"""Returns True if the current audio is in the corresponding shotPkg
		"""
		trackedCamera = self.trackedItem(index)
		if self._shotPkg.cameraPkg:
			return trackedCamera.trackedItemName == self._shotPkg.cameraPkg.name
		return False
	
	def setData(self, index, value, role):
		"""sets editor data in the cell whether to remove or update the camera
		"""
		if not index.isValid() or role != QtCore.Qt.EditRole:
			return False
		# if value didn't change no need to set data
		if value == self.trackedItemData(index):
			return False
		# update the cell data
		if value != "N/A":
			self.setUpdateData(index, value)
		else:
			self.setRemoveData(index)
		return True