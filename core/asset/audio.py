### start python 3 migration
from builtins import str
### end python 3 migration

from .assetBase import AssetBase
from mpc.maya.animationTools.SceneManager import mayaSceneUtils

from maya import cmds

from mpc import logging
_log = logging.getLogger()

class Audio(AssetBase):
	"""A class to save tessa audio asset and its related functions"""

	assetTypeName = "audio"
	hubBundle = "audio"
	# display
	display = "Audio"
	toolTip = "Audio"
	iconFile = "SM_icon_audio.svg"

	def __init__(self, name, tessaAsset=None):
		"""
		audio has to have an audio name to initialize
		args: name(str): audio name

		"""
		super(Audio, self).__init__(name, tessaAsset)
		self.hubElement = name
		self.hubPrefix = ""
		self.newHubPrefix = ""

	def gather(self):
		self.topNode = mayaSceneUtils.gatherAudio(self.tessaAsset)
		return self.topNode
		
	def remove(self):
		if self.inScene():
			cmds.lockNode(self.topNode, l=False)
			cmds.delete(self.topNode)

	def update(self):
		"""update the audio version to it's current tessaAsset version
		"""
		if self.tessaAsset.fullPaths:
			cmds.setAttr(self.topNode + ".filename", self.tessaAsset.fullPaths[0].getPath(), type="string")
			if self.hubSet:
				cmds.setAttr(self.hubSet + ".version", self.tessaAsset.version.versionString(), type="string")

	def initScanHubset(self):
		super(Audio, self).initScanHubset()
		if self.hubSet:
			try:
				self.topNode = cmds.sets(self.hubSet, q=True)[0]
			except IndexError:
				_log.warning("Could not find audio node in the scene")