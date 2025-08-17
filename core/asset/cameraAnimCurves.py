from mpc.hubCharacter import hubGather_animCurves as _hubGather_animCurves
from mpc.assetDefinitions._workflow.shot.cameraPkg import CameraPkg
from .assetBase import AssetBase

class AnimCurves(AssetBase):
	display = "animeCurves"
	toolTip = "animeCurves"
	iconFile = "SM_icon_curves.svg"

	def getAssetFromPackage(self, cameraPkg):
		if not isinstance(cameraPkg, CameraPkg):
			raise TypeError

		try:
			animationCurves = cameraPkg.Animation[0].animation
			mmCurves = cameraPkg.Animation[0].matchmove
			return animationCurves or mmCurves
		except Exception:
			return None

	def gather(self, cameraRigHubset):
		animCurves = self.tessaAsset
		if not animCurves:
			return
		_hubGather_animCurves.animCurves(animCurves, cameraRigHubset)