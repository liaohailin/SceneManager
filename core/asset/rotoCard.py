from mpc.standardPackages.gather import rotoCard as _gatherRotoCard
from mpc.assetDefinitions._workflow.shot.cameraPkg import CameraPkg
from .assetBase import AssetBase

class RotoCard(AssetBase):
	display = "rotoCard"
	toolTip = "rotoCard"
	iconFile = "SM_icon_help.svg"

	def getAssetFromPackage(self, cameraPkg):
		if not isinstance(cameraPkg, CameraPkg):
			raise TypeError

		try:
			return cameraPkg.RotoCard[0].rotoCard
		except Exception:
			return None

	def gather(self, hubset):
		rotoCardPkgAsset = self.tessaAsset
		if not rotoCardPkgAsset:
			return
		_gatherRotoCard.hubGather_rotoCardPkg(
			rotoCardPkgAsset.context.job.name,
			rotoCardPkgAsset.context.scene.name,
			rotoCardPkgAsset.context.shot.name,
			rotoCardPkgAsset.name,
			int(rotoCardPkgAsset.version),
		)