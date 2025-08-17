### start python 3 migration
from builtins import str
from builtins import range
### end python 3 migration

from .rigPuppet import RigPuppet
from mpc.assetDefinitions._workflow.shot.cameraPkg import CameraPkg
from mpc.tessa import uri
from mpc.maya.standardPackages import (
	_utils as _mayaStandardPkgUtils,
	cameraPkgPlatesUtils as _cameraPkgPlatesUtils,
)
from mpc.hubCharacter import (
	hubGather_animCurves as _hubGather_animCurves,
	hubUtils_animation as _hubUtils_animation,
)
from mpc.maya.characterPackages import gather as characterPkgGather
from mpc.maya.standardPackages.gather import gatherCameraTypePkg as cameraTypePkgGather
from mpc.standardPackages.gather import (
	utils as _gatherUtils,
	cropViewPlus as _gatherCropViewPlus,
	rotoCard as _gatherRotoCard,
)
from mpc.retime import retimeNodeUtils as _retime
from mpc.maya.hubMaya import (
	contextManagers as _contextManagers,
	hubSets as _hubSets,
	_timelines,
)
from mpc.maya.mayaUtils import (
	decorators as _decorators,
	namespace as _namespaceUtils,
	attributesUtils as _attrUtils,
)


from maya import cmds

from mpc import logging
_log = logging.getLogger()

class CameraRigPuppet(RigPuppet):
	assetTypeName = "rigPuppet"
	hubElementMatch = ["camera[A-Z]\Z"]
	hubBundle = "rigPuppet"
	# display
	display = "cameraRig"
	toolTip = "cameraRig"
	iconFile = "SM_icon_camera.svg"

	def __init__(self, name, tessaAsset=None):
		super(CameraRigPuppet, self).__init__(name, tessaAsset)
		self.hubPrefix = ""

	def getAssetFromPackage(self, cameraPkg):
		if not isinstance(cameraPkg, CameraPkg):
			raise TypeError
		asset = cameraPkg.Camera[0].cameraRig
		self.hubElement = asset.name
		return asset

	def gather(self, cameraPkg):
		cameraRig = self.tessaAsset

		if not cameraRig or not cameraPkg:
			return
	
		namespace = "{}_{}_{}".format(
			cameraPkg.context.job.name, cameraPkg.context.shot.name, cameraPkg.name
		)

		if cameraRig.assetType == "CameraTypePkg":
			cameraRigHubset = cameraTypePkgGather.gatherCameraTypePkg(
				{"uri": uri.fromAssetVersion(cameraRig)},
				cameraRig.CameraRig[0].cameraRig,
				cameraRig.CameraConfig[0].cameraConfig,
				namespace=namespace,
				asReferenced=True,
			)
		elif cameraRig.assetType == "rigPuppet":
			cameraRigHubset = characterPkgGather.rigPuppet(
				cameraRig, namespace=namespace, asReference=True
			)
		else:
			raise TypeError("{} is not CameraTypePkg or rigPuppet".format(cameraRig))

			# Making sure we get the real namespace. In case the rig had already been gathered, Maya will
		# appended number after the namespace when gathering again
		cameraRigNameSpace = _namespaceUtils.Namespace(cameraRigHubset)
		if not cameraRigNameSpace.parent().isRoot():
			namespace = str(cameraRigNameSpace.parent()).replace(
				_namespaceUtils.DELIMITER, ""
			)

		updateCameraPkgSets(cameraRigHubset, cameraPkg.name)

		# Reselect the hubSet contents to put in the cameraPkgHubSet.
		cmds.select(cameraRigHubset, replace=True, noExpand=True)

		# Create a cameraPkg hub set.
		newHubsetName = _hubSets.HubSetName(
			"CameraPkg", cameraPkg.name, None, namespace=namespace
		)
		newCameraPkgHubSet = _hubSets.HubSet(cameraPkg.context.shot, newHubsetName)
		newCameraPkgHubSet.create(cameraRigHubset)

		# Add updated namespace
		cameraPkgHubSet = newCameraPkgHubSet.name

		# Set the version on the cameraPkg
		versionAttribute = "{}.version".format(cameraPkgHubSet)
		cmds.setAttr(versionAttribute, lock=False)
		cmds.setAttr(versionAttribute, str(cameraPkg.version), type="string")

		setMayaFrameRange(cameraPkg)

		return cameraRigHubset

def updateCameraPkgSets(cameraRigHubset, packageName):
	"""Helper function to update the cameraPkg hubSet and its children to the given prefix

	Args:
			cameraRigHubset (str): the name of the cameraRig hubset
			packageName (str): the name of the package to set as the prefix on the different hubSets
	"""
	childrenHubSets = cmds.sets(cameraRigHubset, query=True)

	for childHubSet in childrenHubSets:
		if cmds.nodeType(childHubSet) != "objectSet":
			continue

		hubPrefixAttribute = "{}.hubPrefix".format(childHubSet)
		if cmds.objExists(hubPrefixAttribute):
			prefixName = packageName
			# Forcing matchmove animCurves asset name to be prefixed with 'mm_'
			if (
				_gatherUtils.gatherDiscipline == "matchmove"
				and _attrUtils.getAttrOrNone(childHubSet, "hubBundle") == "animCurves"
			):
				prefixName = "mm_{}".format(prefixName)
			cmds.setAttr(hubPrefixAttribute, prefixName, type="string")


def timeLineToDict(timeline):
    res = {}
    for keyIdx in range(0, len(timeline), 2):
        valueIdx = keyIdx + 1
        value = timeline[valueIdx]
        res[timeline[keyIdx]] = value if value != 'n/a' else None # normalize empty value
    return res


def setMayaFrameRange(cameraPkg):
    # Set the frame range if override is enabled
    if cameraPkg.Camera[0].overrideShotLength:
        configDict = {
            "startFrame": cameraPkg.Camera[0].startFrame,
            "endFrame": cameraPkg.Camera[0].endFrame,
            "overrideShotLength": cameraPkg.Camera[0].overrideShotLength,
        }

        _mayaStandardPkgUtils.setMayaFrameRange(
            configDict=configDict, context=cameraPkg.context.shot
        )
        return

    # Set the frame range base on work start and end frame in shot grid
    timeLine = _timelines.getWorkTimeline(
        cameraPkg.context.scene.name, cameraPkg.context.shot.name
    )
    timeLineDict = timeLineToDict(timeLine)
    workStartStr = timeLineDict.get('workStart', None)
    workEndStr = timeLineDict.get('workEnd', None)
    startFrame = int(float(workStartStr)) if workStartStr else cameraPkg.Camera[0].startFrame
    endFrame = int(float(workEndStr)) if workEndStr else cameraPkg.Camera[0].endFrame
    cmds.playbackOptions(min=startFrame, max=endFrame, aet=endFrame, ast=startFrame)