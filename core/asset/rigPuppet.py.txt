import os
import re
import contextlib as _contextlib

from mpc.tessa import exceptions as tessaExceptions

from mpc.maya.characterPackages import gather as _gather
from mpc.assetDefinitions._workflow.character.animatedCharacterPkg import AnimatedCharacterPkg
from mpc.characterPackages._assetDefinitions.workflow.character.characterPkg import CharacterPkg
from mpc.characterPackages._assetDefinitions.workflow.character.characterTypePkg import CharacterTypePkg
from mpc.maya.animationTools.SceneManager.core import packageUtils
from mpc.maya.animationTools.SceneManager import mayaSceneUtils

from .assetBase import AssetBase

from maya import cmds

from mpc import logging
_log = logging.getLogger()

class RigPuppet(AssetBase):
	"""A class to save tessa rigPuppet asset and its related functions"""

	hubElementMatch = []
	hubElementUnmatch = []
	hubBundle = "rigPuppet"

	def __init__(self, name, tessaAsset=None):
		super(RigPuppet, self).__init__(name, tessaAsset)

	@property
	def topNode(self):
		if self._topNode:
			return self._topNode
		if not self.hubSet:
			_log.warning("couldn't find hubset for this asset")
			return
		self._topNode = mayaSceneUtils.getTopNodeFromSet(self.hubSet, "rigPuppetSet")
		return self._topNode
	
	@topNode.setter
	def topNode(self, value):
		self._topNode = value

	def getAssetHubSet(self):
		matchingHubSet = []
		hubSetInfo = {
			"hubBundle": self.hubBundle,
			"hubPrefix": self.hubPrefix
		}
		hubsets = mayaSceneUtils.getHubSetFromScene(hubSetInfo)
		for hubset in hubsets:
			hubSetAsset = mayaSceneUtils.HubSetAsset(hubset)
			unMatch = False
			for unmatchString in self.hubElementUnmatch:
				if re.search(unmatchString, hubSetAsset.element):
					# hubElement string has unmatch keyword, not likely the one we looking, skip
					unMatch = True
			if unMatch:
				continue
			for matchString in self.hubElementMatch:
				if re.match(matchString, hubSetAsset.element):
					matchingHubSet.append(hubset)
					return matchingHubSet
		return matchingHubSet

	def releasePath(self):
		""" get rigPuppet's release path where it's supposed to be on disc
		"""
		asssetPath = ""
		if self.tessaAsset.assetPath:
			asssetPath = self.tessaAsset.assetPath
		else:
			asssetPath = self.tessaAsset.mayaScene.assetPath
		if not asssetPath:
			return asssetPath
		sceneMA = ""
		sceneMB = ""
		for f in os.listdir(asssetPath):
			if f.endswith(".mb"):
				sceneMB = os.path.join(asssetPath, f)
			if f.endswith(".ma"):
				sceneMA = os.path.join(asssetPath, f)
		if sceneMB:
			return sceneMB
		else:
			return sceneMA

	def gather(self):
		if self.hubPrefix:
			namespace = "{0}:rp".format(self.hubPrefix)
		self.hubSet = _gather.rigPuppet(
			self.tessaAsset,
			prefix=self.hubPrefix,
			namespace=namespace,
			asReference=True
		)
		# manually set hubprefix to self.hubPrefix since
		# _gather.rigPuppet is doing something strange 
		# ends up prefix is something else
		cmds.setAttr("{0}.hubPrefix".format(self.hubSet), self.hubPrefix, type="string")
		return self.hubSet
	
	def update(self):
		"""Update the rig to a new version in the scene
		"""
		if not self.inScene():
			_log.warning("No reference node to update")
			return
		mayaSceneUtils.updateRigReference(self.topNode, self.releasePath())
		# using characterPackages' prepare function to get updated rig ready
		# what it does is updating related hubsets of rigs to the according tessa asset
		_gather.prepareRig(self.topNode, self.tessaAsset)

	def remove(self):
		"""remove the rig from the scene
		"""
		mayaSceneUtils.deleteReferenceNode(self.topNode)
		self.hubSet = ""
		self.topNode = ""

	def updateHubset(self):
		if not self.hubSet:
			return
		if self.hubPrefix!=cmds.getAttr("{0}.hubPrefix".format(self.hubSet)):
			cmds.setAttr("{0}.hubPrefix".format(self.hubSet), self.hubPrefix, type="string")

class BodyRigPuppet(RigPuppet):
	def __init__(self, tessaAsset=None):
		super(BodyRigPuppet, self).__init__(tessaAsset)

	def getAssetFromPackage(self, package):
		if isinstance(package, AnimatedCharacterPkg):
			cp = packageUtils.CPfromACP(package)
			return self.getAssetFromPackage(cp)
		elif isinstance(package, CharacterPkg):
			pass
		else:
			_log.warning("Not sure how to open this package.")
			return None

		rigPuppetKey = '' #rigPuppetKey to designate which rig to use
		cp = package
		try:
			rigPuppetKey = cp.RigPuppet[0].rigPuppetKey.key
		except AttributeError as ex:
			_log.warning(ex)
			_log.warning("Can't find rigPuppetKey for CharacterTypePkg {0}".format(cp))

		ctp = packageUtils.CTPfromCP(cp)
		if not ctp:
			_log.warning("Invalid characterTypePkg. Aborting!")
			return None
		if not ctp.RigPuppet:
			_log.warning(
				"The field RigPuppet in characterTypePkg {ctp} is empty or doesn't exist".format(
					ctp=ctp.name
				)
			)
			return None
		rigToUse = None
		if not rigPuppetKey:
			try:
				rigToUse = ctp.RigPuppet[0]
			except IndexError as ex:
				_log.error("Can't find rigpuppet in {0}".format(ctp))
				raise
		else:
			for rig in ctp.RigPuppet:
				try:
					rigKey = rig.key
				except AttributeError as ex:
					_log.error("No key value for rig {0}".format(rig))
					continue
				else:
					if rigKey == rigPuppetKey:
						rigToUse = rig
						break
		if not rigToUse:
			_log.warning("Designated rig {0} doesn't exist! Aborting!".format(rigPuppetKey))
			return None
		puppet = getattr(rigToUse, self.assetTypeName, None)
		return puppet


class HighBodyRigPuppet(BodyRigPuppet):
	assetTypeName = "rigPuppet"
	hubElementMatch = ["[a-z0-9A-Z]*[A-Z]\Z"]
	hubElementUnmatch = ["Low[A-Z]\Z"]
	# display
	display = "HB"
	toolTip = "high res body rig"
	iconFile = "SM_icon_body.svg"
	def __init__(self, tessaAsset=None):
		super(HighBodyRigPuppet, self).__init__(tessaAsset)


class LowBodyRigPuppet(BodyRigPuppet):
	assetTypeName = "lowRigPuppet"
	hubElementMatch = ["[a-z0-9A-Z]*Low[A-Z]\Z"]
	# display
	display = "LB"
	toolTip = "low res body rig"
	iconFile = "SM_icon_bodyLowRes.svg"
	def __init__(self, tessaAsset=None):
		super(LowBodyRigPuppet, self).__init__(tessaAsset)


class FaceRigPuppet(RigPuppet):
	def __init__(self, tessaAsset=None):
		super(FaceRigPuppet, self).__init__(tessaAsset)

	def getAssetFromPackage(self, package):
		if isinstance(package, AnimatedCharacterPkg):
			cp = packageUtils.CPfromACP(package)
			return self.getAssetFromPackage(cp)
		elif isinstance(package, CharacterPkg):
			ctp = packageUtils.CTPfromCP(package)
			return self.getAssetFromPackage(ctp)
		elif isinstance(package, CharacterTypePkg):
			pass
		else:
			_log.warning("Not sure how to open this package.")
			return None
		ctp = package
		if not ctp:
			return None
		if not ctp.FacialRigPuppet or not len(ctp.FacialRigPuppet):
			return None
		if not ctp.FacialRigPuppet[0].facialRigPuppet:
			return None
		try:
			puppet = getattr(ctp.FacialRigPuppet[0], self.assetTypeName, None)
		except tessaExceptions.DataProviderKeyError:
			puppet = None
		return puppet


class HighFaceRigPuppet(FaceRigPuppet):
	assetTypeName = "facialRigPuppet"
	hubElementMatch = ["[a-z0-9A-Z]*[A-Z]Facial\Z"]
	hubElementUnmatch = ["Low"]
	# display
	display = "HF"
	toolTip = "high res facial rig puppet"
	iconFile = "SM_icon_facial.svg"
	def __init__(self, tessaAsset=None):
		super(HighFaceRigPuppet, self).__init__(tessaAsset)


class LowFaceRigPuppet(FaceRigPuppet):
	assetTypeName = "lowFacialRigPuppet"
	hubElementMatch = ["[a-z0-9A-Z]*Low[A-Z]Facial\Z", "[a-z0-9A-Z]*LowFacial\Z"]
	# display
	display = "LF"
	toolTip = "low res facial rig puppet"
	iconFile = "SM_icon_facialLowRes.svg"
	def __init__(self, tessaAsset=None):
		super(LowFaceRigPuppet, self).__init__(tessaAsset)


class RigResManager(object):
	def __init__(self, highRig, lowRig):
		super(RigResManager, self).__init__()
		self.high = highRig
		self.low = lowRig
		self.rig = None

	@property
	def rig(self):
		# decide what res of rig to return
		# 0. if self._rig already existed return directly
		if self._rig:
			return self._rig
		# 1. if there is a rig in scene
		if self.high and self.high.inScene():
			self._rig = self.high
		elif self.low and self.low.inScene():
			self._rig = self.low
		# 2. if no rig is in scene
		elif self.high and self.high.ifGather:
			self._rig = self.high
		elif self.low and self.low.ifGather:
			self._rig = self.low
		return self._rig

	@rig.setter
	def rig(self, rigIn):
		self._rig = rigIn

	def ifSwitchRes(self):
		switchRes = False
		if self.high and self.low:
			if self.high.ifRemove and self.low.ifGather:
				switchRes = True
			elif self.low.ifRemove and self.high.ifGather:
				switchRes = True
		return switchRes

	def switchRes(self):
		previousRig = self.rig
		if self.rig==self.high:
			self.rig = self.low
		elif self.rig==self.low:
			self.rig = self.high
		if previousRig.inScene():
			self.rig.gather()
			mayaSceneUtils.transferAnimTopNode(previousRig.topNode, self.rig.topNode)
			previousRig.remove()


class BodyFaceConnector(object):
	def __init__(self, bodyRig, faceRig):
		super(BodyFaceConnector, self).__init__()
		self.bodyRig = bodyRig
		self.faceRig = faceRig

	def _isConnected(self):
		"""is body rig connected with face rig currently?"""
		isConnected = False
		if self.bodyRig and self.bodyRig.topNode and cmds.objExists(self.bodyRig.topNode):
			#TODO: need to find a way to decide if body and rig puppet are connected
			namespace = mayaSceneUtils.getNodeNamespace(self.bodyRig.topNode)
			facial_LOC = namespace + "facial_LOC"
			if cmds.objExists(facial_LOC):
				connectedFacialLoc = cmds.listConnections(facial_LOC, s=True, d=False, scn=True)
				if connectedFacialLoc:
					isConnected = True
		return isConnected
	
	def _connectRig(self):
		if (
			self.bodyRig and self.bodyRig.topNode and cmds.objExists(self.bodyRig.topNode) and 
			self.faceRig and self.faceRig.topNode and cmds.objExists(self.faceRig.topNode)
		):
			bodyTopNode = self.bodyRig.topNode
			faceTopNode = self.faceRig.topNode
			mayaSceneUtils.connectRigs(bodyTopNode, faceTopNode)
			mayaSceneUtils.connectRigs(faceTopNode, bodyTopNode)

	def _disconnectRig(self):
		"""connect body and face rig together"""
		if self.bodyRig and self.faceRig:
			bodyTopNode = self.bodyRig.topNode
			faceTopNode = self.faceRig.topNode
			#When disconnect facial and body rig puppet,
			#we want to skip those nodes that can't find a according target,
			#or it can't be connect back after been disconnected.
			nodesToSkipDisconnect = mayaSceneUtils.getNodesToSkipInDisconnection(bodyTopNode, faceTopNode) +\
			mayaSceneUtils.getNodesToSkipInDisconnection(faceTopNode, bodyTopNode)
			_log.warning("Nodes to Skip: {0}".format(nodesToSkipDisconnect))
			with mayaSceneUtils.addSkipDisconnectAttribute(nodesToSkipDisconnect):
				mayaSceneUtils.disconnectRigs(bodyTopNode, faceTopNode)
				mayaSceneUtils.disconnectRigs(faceTopNode, bodyTopNode)
	
	#-----------------------api methods---------------------
	def updateRigConnection(self, connect=True):
		if connect:
			if not self._isConnected():
				self._connectRig()
		else:
			if self._isConnected():
				self._disconnectRig()
	
	@_contextlib.contextmanager
	def rigDisconnected(self, disconnect=True):
		""" Disconnect facial and body rig and reconnect back after operations.

			Args:
				disconnect (boolean): could choose to disconnect or not on condition
		"""
		if disconnect:
			self.updateRigConnection(connect=False)
			try:
				yield
			finally:
				self.updateRigConnection(connect=True)
		else:
			yield