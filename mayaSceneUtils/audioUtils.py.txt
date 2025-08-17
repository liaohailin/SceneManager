import maya.cmds as cmds

from mpc.standardPackages.gather.audio import hubGather_audio
from mpc import logging

_log = logging.getLogger()

def gatherAudio(audioAsset):
	"""gathers audio file in Maya and returns the audio node name
		args:
			audioAsset (tessa asset): audio asset to be used to get the file path
	"""
	hubset = hubGather_audio(audioAsset.context.job.name, audioAsset.context.scene.name, audioAsset.context.name,
							"audio", audioAsset.name, audioAsset.version._version)
	if hubset:
		# update the scene and shot on the hubset
		sceneAttr = "{}.hubScene".format(hubset)
		shotAttr = "{}.hubShot".format(hubset)
		cmds.setAttr(sceneAttr, lock=False)
		cmds.setAttr(shotAttr, lock=False)
		cmds.setAttr(sceneAttr, audioAsset.context.scene.name, type="string")
		cmds.setAttr(shotAttr, audioAsset.context.name, type="string")
		cmds.setAttr(sceneAttr, lock=True)
		cmds.setAttr(shotAttr, lock=True)
		# try to return the audio node name, otherwise a None would be return
		try:
			return cmds.sets(hubset, q=True)[0]
		except IndexError:
			_log.warning("Could not find audio node in the scene")