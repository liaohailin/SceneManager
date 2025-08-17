from mpc import logging

import sys

from mpc.maya.animationTools.SceneManager.ui import sceneManagerWidget


_log = logging.getLogger()  # type: logging.Logger

class SceneManagerMaya(object):

	instance = None

	@staticmethod
	def showUI():
		if not SceneManagerMaya.instance:
			SceneManagerMaya.instance = sceneManagerWidget.SceneManagerWidget()
			SceneManagerMaya.instance.closed.connect(SceneManagerMaya.onUIClosed)
		SceneManagerMaya.instance.show()

	@staticmethod
	def debugReload():
		""" Reloads the Python modules of the releaseWizard
		"""
		# Close the user interface before reloading the modules to make sure all the scene observers are unregistered.
		if SceneManagerMaya.instance:
			SceneManagerMaya.instance.close()

		# delete all imported modules so that they get reimported
		modes = []
		for mod in sys.modules:
			if mod.startswith("mpc.maya.animationTools.SceneManager"):
				modes.append(mod)
		for mod in modes:
			del sys.modules[mod]

	@staticmethod
	def onUIClosed():
		SceneManagerMaya.instance = None