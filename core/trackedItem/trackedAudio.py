from mpc.maya.animationTools.SceneManager.core.trackedItem import trackedItemBase as _trackedItemClass
from mpc.maya.animationTools.SceneManager.core.asset import audio as _audio

class TrackedAudio(_trackedItemClass.TrackedItem):
	def __init__(self, trackedItemName, hubElement="", tessaAsset=None):
		super(TrackedAudio, self).__init__()
		self.trackedItemName = trackedItemName
		self.audio =_audio.Audio(self.trackedItemName, tessaAsset=tessaAsset)
		self.packageAsset = self.audio
		self.interactiveAssetAttrs = ["audio"]
		self.updateList = []
		self.hubPrefix = ""
		self.hubElement = trackedItemName
		if hubElement:
			self.hubElement = hubElement
	
	@classmethod
	def copy(cls, originalItem):
		newItem = cls(
			originalItem.trackedItemName, tessaAsset=originalItem.packageAsset.tessaAsset)
		return cls.copyHelper(originalItem, newItem)

	def processAssets(self):
		if not self.updateList:
			return
		self.updateAsset(self.audio)
		self.resetFlags()

class UpdateAudio(TrackedAudio):
	"""A class to represent the audio node on the Manage tab of the UI. This is used to update the audio version.
	"""
	def __init__(self, trackedItemName, tessaAsset=None):
		"""initialize the instance with the audio node name, corresponding tessa asset and hubset
		"""
		super(UpdateAudio, self).__init__(trackedItemName, tessaAsset)
		self.hubElement = trackedItemName
		self.hubPrefix = ""
		self.interactiveAssetAttrs = ["packageAsset", "audio"]
		self.audio.initScanHubset()