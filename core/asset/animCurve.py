from mpc.hubCharacter import hubGather_animCurves as _hubGather
from mpc.assetDefinitions._workflow.character.animatedCharacterPkg import AnimatedCharacterPkg
from mpc.maya.mayaUtils import attributesUtils as _attributesUtils

from .assetBase import AssetBase
from mpc.maya.animationTools.SceneManager import mayaSceneUtils

import re

from maya import cmds

from mpc import logging
_log = logging.getLogger()

class AnimCurve(AssetBase):
	"""A class to save tessa animCurve asset and its related functions"""
	
	hubBundle = "animCurves"
	hubElementMatch = []
	hubElementUnmatch = []

	def __init__(self, name, tessaAsset=None, ifRelease=False):
		super(AnimCurve, self).__init__(name, tessaAsset)
		# if this anim curve object is a release anim curve
		# gather anim curve and release anim curve has different behaviour when update
		self.ifRelease = ifRelease
		self.rigManager = None # reference to rig manager

	def getAssetFromPackage(self, package):
		if not isinstance(package, AnimatedCharacterPkg):
			_log.warning("Not sure how to open this package.")
			return None
		acp = package
		if not acp.Animation or not len(acp.Animation):
			return None
		animCurve = getattr(acp.Animation[0], self.assetTypeName, None)
		return animCurve

	def getAssetHubSet(self):
		matchingHubSet = []
		hubSetInfo = {
			"hubBundle": self.hubBundle
		}
		if not self.rigManager.rig:
			return []
		#get childset from righubset
		members = cmds.sets(self.rigManager.rig.hubSet, query=True)
		memberSets = [member for member in members if cmds.objectType(member) == 'objectSet']
		hubsets = mayaSceneUtils.getHubSetFromScene(hubSetInfo, setList=memberSets)
		for hubset in hubsets:
			if self.ifRelease:
				if _attributesUtils.getAttrOrNone(hubset, "hubInfoSet"):
					continue
			else:
				if cmds.ls(hubset, rn=True):
					# continue if it's a referenced node
					continue
				if not _attributesUtils.getAttrOrNone(hubset, "hubInfoSet"):
					continue
				if "Gather" not in hubset:
					continue
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

	def gather(self):
		if self.ifRelease:
			# release anim curve come automatically with rigpuppet so no need to gather
			return
		if not self.rigManager.rig:
			return
		animCurves = self.tessaAsset
		namespace = "{0}:ac".format(self.hubPrefix)
		with mayaSceneUtils.switchNamespace(namespace):
			animCurvesHubSet = _hubGather.hubGather_animCurves(
				animCurves.context.job.name,
				animCurves.context.scene.name,
				animCurves.context.shot.name,
				animCurves.assetType,
				animCurves.name,
				int(animCurves.version),
				self.rigManager.rig.topNode,
				services=animCurves.services
			)
		self.hubSet = animCurvesHubSet

	def updateHubset(self):
		if not self.inScene():
			return
		if self.ifRelease:
			if self.hubPrefix!=cmds.getAttr("{0}.hubPrefix".format(self.hubSet)):
				cmds.setAttr("{0}.hubPrefix".format(self.hubSet), self.hubPrefix, type="string")
		# make sure hubset is inside rigPuppet hubset
		# if not add it to rigPuppet
		if self.rigManager.rig.hubSet:
			mayaSceneUtils.addToSet(self.rigManager.rig.hubSet, self.hubSet)
		else:
			#remove anim curve hubset if rigpuppet not existed anymore
			self.remove()

	def update(self):
		if self.ifRelease:
			return
		# can only delete hubset that has hubInfoSet checked
		if self.hubSet and _attributesUtils.getAttrOrNone(self.hubSet, "hubInfoSet"):
			cmds.delete(self.hubSet)
		self.hubSet = ""
		self.gather()

	def remove(self):
		# remove gathered anim curve hubset
		if self.inScene():
			cmds.lockNode(self.hubSet, l=False)
			cmds.delete(self.hubSet)


class BodyAnimCurve(AnimCurve):
	"""A class to save tessa animCurve asset and its related functions"""
	assetTypeName = "animation"
	hubElementMatch = ["[a-z0-9A-Z]*[A-Z]\Z"]
	hubElementUnmatch = ["Facial\Z"]
	# display
	display = "BC"
	toolTip = "animation curve"
	iconFile = "SM_icon_curves.svg"

	def __init__(self, tessaAsset):
		super(BodyAnimCurve, self).__init__(tessaAsset)

class FaceAnimCurve(AnimCurve):
	"""A class to save tessa animCurve asset and its related functions"""
	assetTypeName = "facialAnimation"
	hubElementMatch = ["[a-z0-9A-Z]*[A-Z]Facial\Z"]
	# display
	display = "FC"
	toolTip = "facial animation curve"
	iconFile = "SM_icon_curves.svg"
	def __init__(self, tessaAsset):
		super(FaceAnimCurve, self).__init__(tessaAsset)