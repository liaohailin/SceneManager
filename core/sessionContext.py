from mpc.tessa import store

from mpc import logging
_log = logging.getLogger()


def CTPfromCP(cp):
	if not cp:
		return None
	if not cp.CharacterType or not len(cp.CharacterType):
		_log.warning("The field CharacterType in CP {} is empty".format(cp.name))
		return None

	if not cp.CharacterType[0].characterType:
		_log.warning("The field charactertype in the first row of the CharacterType of CP {} is empty".format(
						cp.name))
		return None
	return cp.CharacterType[0].characterType


def CPfromACP(acp):
	if not acp:
		_log.debug("No CP found for {asset}".format(asset=acp.name))
		return None
	
	if hasattr(acp, "Character"):
		if not acp.Character or not len(acp.Character):
			_log.warning("The field Character in ACP {} is empty in".format(acp.name))
			return None
	else:
		_log.warning("The field Character in ACP {} does not exist".format(acp.name))
		return None

	if hasattr(acp.Character[0], "character"):
		if not acp.Character[0].character:
			_log.warning("The field character in the first row of the Character of ACP {} is empty".format(
							acp.name))
			return None
	else:
		_log.warning("The field character in the first row of the Character of ACP {} does not exist".format(
							acp.name))
		return None 

	return acp.Character[0].character


def ACPfromShotPkg(shotPkg):
	acps = []
	if not shotPkg:
		return acps
	if not shotPkg.Layout or not len(shotPkg.Layout):
		_log.warning("Invalid/Empty layout package in ShotPkg {}!".format(shotPkg.name))
	for layoutMember in shotPkg.Layout[0].Cast.layoutMembers:
		if not layoutMember:
			_log.warning("Invalid/Empty layoutMember in shotPkg {}, skipped".format(shotPkg.name))
			continue
		acp = layoutMember[2].value
		if not acp:
			_log.warning("Invalid/Empty ACP in shotPkg {}, skipped".format(shotPkg.name))
			continue
		acps.append(acp)
	return acps

def getShotPkg(context, stream):
	shotPkgs = store.findAssets(context, assetType="ShotPkg")
	shotPkgAssets = [shotPkg for shotPkg in shotPkgs if shotPkg.stream.name == stream]
	if not shotPkgAssets:
		_log.warning("Can't find proper shotPkg for designated shot")
		return
	return shotPkgAssets[0]


class CameraRepository(object):
	@staticmethod
	def generator(context):
		for camera in store.findAssets(context, assetType="CameraPkg"):
			latestCamera = camera.gather(store.vLatest)

			if CameraRepository.isLegacyCamera(latestCamera):
				continue

			yield latestCamera

	@staticmethod
	def isLegacyCamera(camera):
		return camera.Camera[0].camera is not None