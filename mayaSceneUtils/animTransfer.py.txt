from maya import mel
import pymel.core as pm

from mpc import logging

_log = logging.getLogger()


def transferAnimTopNode(sourceTopNode, targetTopNode):
	if sourceTopNode and targetTopNode:
		sourceCtrls = mel.eval('rig_animToolsSelectRigControls({{"{0}"}}, "", "");'.format(sourceTopNode))
		targetCtrls = mel.eval('rig_animToolsSelectRigControls({{"{0}"}}, "", "");'.format(targetTopNode))
		sourceGlobalCtrl = mel.eval('rig_animToolsSelectRigControls({{"{0}"}}, "{1}", "");'.format(sourceTopNode, "*global_CTRL"))
		targetGlobalCtrl = mel.eval('rig_animToolsSelectRigControls({{"{0}"}}, "{1}", "");'.format(targetTopNode, "*global_CTRL"))
		sourceSpineCtrl = mel.eval('rig_animToolsSelectRigControls({{"{0}"}}, "{1}", "");'.format(sourceTopNode, "*spineFullBody_CTRL"))
		targetSpineCtrl = mel.eval('rig_animToolsSelectRigControls({{"{0}"}}, "{1}", "");'.format(targetTopNode, "*spineFullBody_CTRL"))

		#first transfer global control anim
		if sourceGlobalCtrl and targetGlobalCtrl:
			globalCtrlPairs = getControlObjPairs(sourceGlobalCtrl, targetGlobalCtrl)
			connectCurveSourceToTarget(globalCtrlPairs)

		#then transfer spine control anim
		if sourceSpineCtrl and targetSpineCtrl:
			globalSpinePairs = getControlObjPairs(sourceSpineCtrl, targetSpineCtrl)
			connectCurveSourceToTarget(globalSpinePairs)

		# then transfer other controls
		if sourceCtrls and targetCtrls:
			controlObjPairs = getControlObjPairs(sourceCtrls, targetCtrls)
			connectCurveSourceToTarget(controlObjPairs)
		else:
			_log.warning("couldn't get controls to transfer anim.")
	else:
		_log.warning("couldn't get source or target rigPuppet node.")


def getControlObjPairs(sourceCtrls, targetCtrls):
	""" Get pairs of source->target controls
		Args:
			sources(list of node long names)
			targets(list of node long names)
		returns:
			outputCtrlObjPairs(list of tuple): [(source:body_ctrl, target:body_ctrl), ...]
	"""
	targetNamespace = pm.PyNode(targetCtrls[0]).namespace()
	outputCtrlObjPairs = []
	for each in sourceCtrls:
		ctrlName  = each.split(":")[-1]
		potentialTargetCtrl = "{0}{1}".format(targetNamespace, ctrlName)
		if "{0}{1}".format(targetNamespace, ctrlName) in targetCtrls:
			outputCtrlObjPairs.append((pm.PyNode(each), pm.PyNode(potentialTargetCtrl)))
	return outputCtrlObjPairs


def connectCurveSourceToTarget(ctrlPairs):
	""" Connect anim curve from source objects to target objects
		Args:
			ctrlPairs(list of tuple containing PyNode objs): [(source:body_ctrl, target:body_ctrl), ...]
	"""
	# first connect object together
	for source, target in ctrlPairs:
		# set attribute first
		# redirect anim curve
		curveControlConnectPair = pm.listConnections(source, type=["animCurveTL", "animCurveTA", "animCurveTU", "animBlendNodeBase", "animLayer"], plugs=True, c=True, s=True, d=False)
		controlCurveConnectPair = pm.listConnections(source, type=["animCurveTL", "animCurveTA", "animCurveTU", "animBlendNodeBase", "animLayer"], plugs=True, c=True, s=False, d=True)

		for controlAttr, curveAttr in curveControlConnectPair:
			try:
				curveAttr>>pm.PyNode("{0}.{1}".format(target, controlAttr.attrName()))
			except Exception as ex:
				_log.debug(ex)
			else:
				_log.debug("success connect {0} -> {1}".format(curveAttr, target))
		for controlAttr, curveAttr in controlCurveConnectPair:
			try:
				pm.PyNode("{0}.{1}".format(target, controlAttr.attrName()))>>curveAttr
			except Exception as ex:
				_log.debug(ex)
			else:
				_log.debug("success connect {0} -> {1}".format(target, curveAttr))

	# then transfer other attributes
	for source, target in ctrlPairs:
		targetAttrs = [attr.attrName() for attr in target.listAttr(
			keyable=True, unlocked=True, settable=True, visible=True, connectable=True)]
		for sourceAttr in source.listAttr(keyable=True, unlocked=True, settable=True, visible=True, connectable=True):
			if sourceAttr.attrName() in targetAttrs:
				targetAttr = target.attr(sourceAttr.attrName())
				try:
					targetAttr.set(sourceAttr.get())
				except Exception as ex:
					_log.debug(ex)