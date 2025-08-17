### start python 3 migration
from builtins import str
### end python 3 migration
from mpc.maya.standardPackages import cameraPkgPlatesUtils as _cameraPkgPlatesUtils
from mpc.assetDefinitions._workflow.shot.cameraPkg import CameraPkg
from mpc.standardPackages.gather.CameraPkg import getPlatesData
from .assetBase import AssetBase

class PlatesTessaAsset(dict):
	@property
	def assets(self):
		return [plateTuple[0] for plateTuple in self.values()]

	@property
	def version(self):
		versions = [str(plate.version) for plate in self.assets]
		return "/".join(versions)

	@property
	def name(self):
		names = [plate.name for plate in self.assets]
		return "/".join(names)

	def __hash__(self):
		ids = [str(plate) for plate in self.assets]
		return hash("/".join(ids))

class Plates(AssetBase):
	display = "plates"
	toolTip = "plates"
	iconFile = "SM_icon_plates.svg"

	def getAssetFromPackage(self, cameraPkg):
		if not isinstance(cameraPkg, CameraPkg):
			raise TypeError

		try:
			platesDict = getPlatesData(cameraPkg)
			return PlatesTessaAsset(platesDict) if platesDict else None
		except Exception:
			return None

	def gather(self, cameraRigHubset):
		plates = self.tessaAsset
		if not plates:
			return
		_cameraPkgPlatesUtils.gatherPlates(plates, cameraRigHubset)