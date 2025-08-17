### start python 3 migration
from builtins import str
### end python 3 migration

from mpc.maya.mayaUtils import contexts as _mayaContexts
from mpc.maya.hubMaya import hubSets as _hubMayaSets
from mpc.maya.characterPackages import gather as _gather

from mpc.maya.animationTools.SceneManager.core.asset.assetBase import AssetBase
from mpc.maya.animationTools.SceneManager import mayaSceneUtils

from maya import cmds

from mpc import logging
_log = logging.getLogger()

class CameraPkg(AssetBase):
	"""A class to save tessa CameraPkg asset and its related functions"""

	assetTypeName = "CameraPkg"
	hubBundle = "CameraPkg"
	# display
	display = "CameraPkg"
	toolTip = "CameraPkg"

	def __init__(self, name, tessaAsset=None):
		super(CameraPkg, self).__init__(name, tessaAsset)
		"""
		CP has to have an cp name to initialize
		args: name(str): cp name

		"""
		self.hubElement = name
		self.hubPrefix = ""
		self.newHubPrefix = ""
	
	def gather(self, hubsets):
		"""gather CameraPkg is just creating a hubset with rigPuppet hubset in it
		"""
		if not self.tessaAsset:
			raise RuntimeError("can't get hubset of {0}.".format(self.assetTypeName))
		# 1. generate namespace
		namespace = "{}_{}_{}".format(self.tessaAsset.job.name, self.tessaAsset.shot.name, self.hubElement)
		# 2. create hubset and add nodes to it
		cameraPkgHubsetName = _hubMayaSets.HubSetName(
			self.hubBundle, 
			self.hubElement, self.tessaAsset.stream
		)
		cameraPkgHubSet = _hubMayaSets.HubSet(
			self.tessaAsset.context,
			cameraPkgHubsetName,
			version=str(self.tessaAsset.version)
		)
		with mayaSceneUtils.switchNamespace(namespace):
			cameraPkgHubSet.create(hubsets)
		self.hubSet = "{0}:{1}".format(namespace, cameraPkgHubSet.name)
		# add hubPrefix if there is no such attribute
		_gather._safeAddAndSetAttribute(
			self.hubSet,
			"hubPrefix", self.hubPrefix, 
			False, #if reference
			dataType="string"
		)

	def updateHubset(self, hubsets):
		"""updates the hubsets with data from new tessaAsset
		"""
		# add all hubsets to acp hubset
		mayaSceneUtils.addToSet(self.hubSet, hubsets)
		#if self.hubPrefix!=cmds.getAttr("{0}.hubPrefix".format(self.hubSet)):
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
		
	def remove(self):
		"""remove hubset from the scene
		"""
		if self.inScene():
			cmds.lockNode(self.hubSet, l=False)
			cmds.delete(self.hubSet)