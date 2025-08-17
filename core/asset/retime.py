from mpc.hubCharacter import hubUtils_animation as _hubUtils_animation
from mpc.retime import retimeNodeUtils as _retime
from mpc.assetDefinitions._workflow.shot.cameraPkg import CameraPkg
from .assetBase import AssetBase

class Retime(AssetBase):
	display = "retime"
	toolTip = "retime"
	iconFile = "SM_icon_help.svg"
	
	def getAssetFromPackage(self, cameraPkg):
		if not isinstance(cameraPkg, CameraPkg):
			raise TypeError

		try:
			return cameraPkg.Retime[0].retime
		except Exception:
			return None

	def gather(self, cameraRigHubset):
		retimeAsset = self.tessaAsset
		if not retimeAsset:
			return
		retimeNode, retimeNodeHubSet = _retime.gatherRetimeInfoAsset(retimeAsset)
		cameraTopNode = _hubUtils_animation.getTopNode(cameraRigHubset)
		_retime.connectRetimeToObject(retimeNode, cameraTopNode)