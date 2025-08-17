from mpc.maya.animationTools.SceneManager.core.trackedItem import trackedItemBase as _trackedItemClass

from mpc.maya.animationTools.SceneManager.core.packageAsset import cameraPkg as _cameraPkg
from mpc.maya.animationTools.SceneManager.core.asset import cameraRig as _cameraRig
from mpc.maya.animationTools.SceneManager.core.asset import rotoCard as _rotoCard
from mpc.maya.animationTools.SceneManager.core.asset import retime as _retime
from mpc.maya.animationTools.SceneManager.core.asset import plates as _plates
from mpc.maya.animationTools.SceneManager.core.asset import cameraAnimCurves as _cameraAnimCurves

class TrackedCameraPkg(_trackedItemClass.TrackedItem):

	def __init__(self, trackedItemName, hubElement="", tessaAsset=None):
		super(TrackedCameraPkg, self).__init__()
		self.trackedItemName = trackedItemName
		self.hubElement = trackedItemName
		if hubElement:
			self.hubElement = hubElement
		self.hubPrefix = ""
		self.packageAsset = _cameraPkg.CameraPkg(self.trackedItemName, tessaAsset=tessaAsset)
		
		self.interactiveAssetAttrs = [
				"packageAsset",
				"cameraRig",
				"animCurves",
				"plates",
				#"retime",
				#"rotoCard"
		]
		self.cameraRig = _cameraRig.CameraRigPuppet(self.trackedItemName)
		self.animCurves = _cameraAnimCurves.AnimCurves(self.trackedItemName)
		self.plates = _plates.Plates(self.trackedItemName)
		self.retime = _retime.Retime(self.trackedItemName)
		self.rotoCard = _rotoCard.RotoCard(self.trackedItemName)

		if self.packageAsset.tessaAsset:
			self.cameraRig.initFromPkg(self.packageAsset.tessaAsset)
			self.animCurves.initFromPkg(self.packageAsset.tessaAsset)
			self.plates.initFromPkg(self.packageAsset.tessaAsset)
			self.retime.initFromPkg(self.packageAsset.tessaAsset)
			self.rotoCard.initFromPkg(self.packageAsset.tessaAsset)

		self.updateList = []
	
	@classmethod
	def copy(cls, originalItem):
		newItem = cls(
				originalItem.trackedItemName, tessaAsset=originalItem.packageAsset.tessaAsset)
		return cls.copyHelper(originalItem, newItem)

class GatherCameraPkg(TrackedCameraPkg):
	"""Class to represent the gather camera item on the gather tab
	"""
	
	def updateCamera(self):
		if not self.packageAsset:
			return
		# TODO: refactor this
		cameraRigHubSet = self.cameraRig.gather(self.packageAsset.tessaAsset)
		if self.animCurves.ifGather:
			self.animCurves.gather(cameraRigHubSet)
		if self.plates.ifGather:
			self.plates.gather(cameraRigHubSet)
		if self.retime.ifGather:
			self.retime.gather(cameraRigHubSet)
		if self.rotoCard.ifGather:
			self.rotoCard.gather(cameraRigHubSet)
		
		asset = self.packageAsset
		if asset.ifGather:
			asset.gather()
		if asset.ifUpdate:
			asset.update()
		if asset.ifRemove:
			asset.remove()
		del self.updateList[:]
	
	def processAssets(self):
		if not self.updateList:
			return
		self.updateCamera()
		self.resetFlags()

class UpdateCameraPkg(TrackedCameraPkg):
	"""class to represent update camera item on the manage tab
	"""

	def __init__(self, trackedItemName, hubElement="", tessaAsset=None):
		super(UpdateCameraPkg, self).__init__(trackedItemName, hubElement=hubElement, tessaAsset=tessaAsset)
		self.interactiveAssetAttrs = [
			"packageAsset",
			"cameraRig"
		]
		self.packageAsset.initScanHubset()
		self.cameraRig.initScanHubset()
	
	def _updateCameraRigPuppet(self):
		"""updates the camera rig puppet in the scene
		"""
		if self.cameraRig in self.updateList:
			self.updateAsset(self.cameraRig)
	
	def _updateCameraPkg(self):
		"""updates the cameraPkg in the scene
		"""
		ifGather = False
		ifUpdate = False
		ifRemove = True
		rigHubsets = []
		if not self.packageAsset.hubSet:
			ifGather = True
		else:
			ifUpdate = True

		if self.cameraRig.hubSet:
			rigHubsets.append(self.cameraRig.hubSet)
		if self.cameraRig.inScene():
			ifRemove = False

		if ifGather:
			self.packageAsset.gather(rigHubsets)
		if ifUpdate:
			self.packageAsset.updateHubset(rigHubsets)
		if ifRemove:
			self.packageAsset.remove()

	def processAssets(self):
		if not self.updateList:
			return
		self._updateCameraRigPuppet()
		self._updateCameraPkg()
		self.resetFlags()

	def hasValidAsset(self):
		for attr in self.interactiveAssetAttrs:
			asset = self.getAsset(attr)
			if asset.tessaAsset:
				return True
		return False