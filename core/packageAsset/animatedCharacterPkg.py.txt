### start python 3 migration
from builtins import str
### end python 3 migration

from mpc.maya.hubMaya import hubSets as _hubMayaSets
from mpc.maya.mayaUtils import contexts as _mayaContexts

from mpc.maya.characterPackages import gather as _gather

from mpc.maya.animationTools.SceneManager.core.asset.assetBase import AssetBase
from mpc.maya.animationTools.SceneManager import mayaSceneUtils

from maya import cmds

class CharacterPkg(AssetBase):
	"""A class to save tessa CharacterPkg asset and its related functions"""

	assetTypeName = "cp"
	hubBundle = "CharacterPkg"
	# display
	display = "CP"
	toolTip = "CharacterPkg"

	def __init__(self, name, hubElement="", tessaAsset=None):
		super(CharacterPkg, self).__init__(name, tessaAsset)
		"""
		CP has to have an cp name to initialize
		args: name(str): cp name

		"""
		self.hubElement = hubElement

	def gather(self, hubsets):
		# gather acp means create a acp hubset
		# 1. generate namespace
		# namespace = {hubElement}:acp
		namespace = "{0}:{1}".format(self.hubPrefix, self.assetTypeName)
		# 2. create hubset and add nodes to it
		if not self.tessaAsset:
			raise RuntimeError("can't get hubset of {0}.".format(self.assetTypeName))
		acpHubsetName = _hubMayaSets.HubSetName(
			self.hubBundle, 
			self.hubElement, self.tessaAsset.stream
		)
		acpHubSet = _hubMayaSets.HubSet(
			self.tessaAsset.context,
			acpHubsetName,
			version=str(self.tessaAsset.version)
		)
		with mayaSceneUtils.switchNamespace(namespace):
			acpHubSet.create(hubsets)
		# add hubPrefix if there is no such attribute
		self.hubSet = "{0}:{1}".format(namespace, acpHubSet.name)
		_gather._safeAddAndSetAttribute(
			self.hubSet, 
			"hubPrefix", self.hubPrefix, 
			False, #if reference
			dataType="string"
		)

	def updateHubset(self, hubsets):
		# add all hubsets to acp hubset
		mayaSceneUtils.addToSet(self.hubSet, hubsets)
		if (
			not cmds.attributeQuery("hubPrefix", node=self.hubSet, exists=True) or
			self.hubPrefix!=cmds.getAttr("{0}.hubPrefix".format(self.hubSet))
		):
			if self.tessaAsset:
				attrs = {
					"hubJob": self.tessaAsset.context.job.name,
					"hubScene": self.tessaAsset.context.scene.name,
					"hubShot": self.tessaAsset.context.shot.name,
					"hubBundle": self.tessaAsset.assetType,
					"hubElement": self.tessaAsset.name
				}
				with _mayaContexts.unlockAttributes(self.hubSet, list(attrs)):
					for attr, value in attrs.items():
						cmds.setAttr("{0}.{1}".format(self.hubSet, attr), value, type="string")
				cmds.setAttr("{0}.version".format(self.hubSet), self.tessaAsset.version, type="string")
			_gather._safeAddAndSetAttribute(
				self.hubSet, 
				"hubPrefix", self.hubPrefix, 
				False, #if reference
				dataType="string"
			)
		
	def remove(self):
		if self.inScene():
			cmds.lockNode(self.hubSet, l=False)
			cmds.delete(self.hubSet)

	def getAssetHubSet(self):
		"""Looking for ACP hubset
		"""
		hubSetInfo = {
			"hubBundle": self.hubBundle
		}
		hubsets = mayaSceneUtils.getHubSetFromScene(hubSetInfo, startName=self.hubPrefix)
		hubsets = [hubset for hubset in hubsets if self.hubPrefix in hubset]
		return hubsets


class AnimatedCharacterPkg(CharacterPkg):
	"""A class to save tessa AnimatedCharacterPkg asset and its related functions"""
	assetTypeName = "acp"
	hubBundle = "AnimatedCharacterPkg"
	# display
	display = "ACP"
	toolTip = "AnimatedCharacterPkg"

	def __init__(self, name, hubElement="", tessaAsset=None):
		super(AnimatedCharacterPkg, self).__init__(name, hubElement=hubElement, tessaAsset=tessaAsset)