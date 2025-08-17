import os
from collections import OrderedDict

from mpc.maya.animationTools.SceneManager.core import exceptions
from mpc.maya.animationTools.SceneManager import mayaSceneUtils
from mpc.tessa import publishing

from maya import cmds

from mpc import logging
_log = logging.getLogger()

class AssetBase(object):
	"""A class to save tessa rigPuppet asset and its related functions"""

	assetTypeName = ""
	hubBundle = ""

	def __init__(self, name, tessaAsset=None):
		# tessa asset
		self.tessaAsset = tessaAsset
		self._assetVersions = OrderedDict()
		self.usePublishedAsset = False
		# hubset and maya scene related attribute
		self.hubSet = ""
		self.hubPrefix = name
		self.newHubPrefix = name
		self.hubElement = ""
		self._topNode = ""
		self._namespace = ""
		# update status
		self.ifGather=False
		self.ifUpdate=False
		self.ifRemove=False

	@property
	def assetVersions(self):
		if not self._assetVersions:
			self._assetVersions.update(self._getAssetVersions(publishedIn=self.usePublishedAsset))
		return self._assetVersions
	
	@property
	def sceneVersion(self):
		"""return this asset's version being used in the scene
		this is not the same as the currentVersion, as currentVersion returns whatever version is underlying
		tessaAsset. tessaAsset gets updated as soon as the comboBox on the manage tab is activated, so
		the version of tessaAsset and the version being used in the scene might differ at times.
		"""
		if self.hubSet:
			return cmds.getAttr("{}.version".format(self.hubSet)).split("v")[-1]

	@property
	def currentVersion(self):
		"""Returns the current version of this asset
		"""
		if self.tessaAsset:
			return int(self.tessaAsset.version)

	@property
	def namespace(self):
		if not self._namespace:
			if self.hubSet:
				self._namespace = mayaSceneUtils.getNodeNamespace(self.hubSet)
		return self._namespace

	def _getAssetVersions(self, publishedIn=False):
		publishedVersions = OrderedDict()
		if self.tessaAsset:
			versions = [int(version) for version in self.tessaAsset.getAsset().findVersions(published=publishedIn)]
			versions.sort(reverse=True)
			for version in versions:
				asset = self.tessaAsset.getAsset().gather(version)
				publishedVersions[int(version)] = True if publishing.fetch(asset).tags() else False
		return publishedVersions

	#----------------------------api methods-------------------------
	# implement by subclasses 
	# TODO: make them abstract classes
	
	def getAssetFromPackage(self, package):
		pass

	def getAssetHubSet(self):
		"""Returns the Maya hubset of this asset
		"""
		hubSetInfo = {
			"hubBundle": self.hubBundle
		}
		if self.hubElement:
			hubSetInfo["hubElement"] = self.hubElement
		if self.hubPrefix:
			hubSetInfo["hubPrefix"] = self.hubPrefix
		hubsets = mayaSceneUtils.getHubSetFromScene(hubSetInfo)
		hubsets = [hubset for hubset in hubsets if self.hubPrefix in hubset]
		return hubsets

	#-----initialization
	def initScanHubset(self):
		"""Initialize the hubset variable with the corresponding huset in Maya
		"""
		for hubset in self.getAssetHubSet():
			hubSetAsset = mayaSceneUtils.HubSetAsset(hubset)
			self.hubSet = hubset
			self.tessaAsset = hubSetAsset.tessaAsset
			break
		else:
			raise exceptions.NoHubSetException("Can't get {0} hubset info from scene!".format(self.assetTypeName))
	
	def initFromPkg(self, package):
		self.tessaAsset = self.getAssetFromPackage(package)

	#-----data fetching and malipulation
	def syncHubPrefix(self):
		self.hubPrefix = self.newHubPrefix

	def changeVersion(self, version):
		"""change current tessa assset to a different version
		args:
			version(int): version number
		"""
		assetVersion = None
		if version != self.currentVersion:
			assetVersion = self.tessaAsset.getAsset().gather(version)
		else:
			# no need to gather asset if the version is not changing
			return
		if not assetVersion:
			_log.error("Failed getting version of the asset")
			return
		self.tessaAsset = assetVersion

	#-----data validation
	def inScene(self):
		if cmds.objExists(self.hubSet):
			return True
		else:
			return False