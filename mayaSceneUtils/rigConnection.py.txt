### start python 3 migration
from builtins import str
### end python 3 migration

from maya import cmds
from maya import mel
import pymel.core as pm

import contextlib as _contextlib

from mpc import logging
_log = logging.getLogger()


def getNodesToSkipInDisconnection(driverTopNode, drivenTopNode):
	""" When facial and body rig puppet get disconnected, nodes will get disconnected with certain method to
		its matching node. However, sometimes there are no matching node(target) to disconnect from.
		If this node is kept disconnected, something else will be disconnected. This function returns these
		nodes that should be skipped.

		Args:
			driverTopNode (str): driver top node
			drivenTopNode (str): driven top node
		Return:
			nodesToSkip (list of str): list of nodes that ought to be skipped when disconnect
	"""
	# calling rig_connectFindNodesToConnect to find the nodes to connect in drivenTopNode
	nodesToConnect = mel.eval("rig_connectFindNodesToConnect(\"{0}\");".format(drivenTopNode))
	# convert the nodes to connect to mel list
	nodesToConnectMelList = "{\"" + "\",\"".join(nodesToConnect) + "\"}"
	# calling rig_connectFindConnectionTargets to find the nodes to connect to(target nodes) in driverTopNode
	nodesToConnectTo = mel.eval("rig_connectFindConnectionTargets({0}, \"{1}\");".format(nodesToConnectMelList, driverTopNode))
	# remove "" from list
	nodesToConnectTo = [node for node in nodesToConnectTo if node]
	nodesToConnectToIDs = set()
	nodesToConnectToMatchNames = set()
	for node in nodesToConnectTo:
		try:
			nodeObj = pm.PyNode(node)
			nodesToConnectToIDs.add(nodeObj.connectID.get())
		except AttributeError as ex:
			_log.warning(ex)
		nodesToConnectToMatchNames.add(str(nodeObj.stripNamespace()))
	# find out which obj doesn't have a connect target and add skip attribute
	nodesToSkip = []
	for node in nodesToConnect:
		nodeObj = pm.PyNode(node)
		connectID = nodeObj.connectID.get()
		if connectID not in nodesToConnectToIDs and\
		connectID not in nodesToConnectToMatchNames and\
		str(nodeObj.stripNamespace()) not in nodesToConnectToMatchNames:
			nodesToSkip.append(node)
	return nodesToSkip


@_contextlib.contextmanager
def addSkipDisconnectAttribute(nodesToSkip):
	""" Add connectMethodSkipDisconnect attribute to some nodes and remove after finish operation

		Args:
			nodesToSkip (list of str): list of nodes that ought to be skipped when disconnect
	"""
	for node in nodesToSkip:
		nodeObj = pm.PyNode(node)
		try:
			nodeObj.addAttr("connectMethodSkipDisconnect", dv=1)
		except RuntimeError as ex:
			_log.warning(ex)
	try:
		yield
	finally:
		for node in nodesToSkip:
			nodeObj = pm.PyNode(node)
			try:
				nodeObj.deleteAttr("connectMethodSkipDisconnect")
			except (pm.MayaAttributeError, RuntimeError) as ex:
				_log.warning(ex)


def disconnectRigs(topNodeDriver, topNodeDriven):
	""" Disconnects rigs by calling the mel function rig_disconnectRigSelected

		Args:
			topNodeDriver (str)
			topNodeDriven (str)

		Returns:
			(bool) the result of rig_disconnectRigSelected (list[str])

	"""
	if not topNodeDriven or not topNodeDriver:
		raise RuntimeError("Can't disconnect rig when top node doesn't exist.")

	cmds.select([topNodeDriver, topNodeDriven], r=True)
	return mel.eval("rig_disconnectRigSelected();")


def connectRigs(topNodeDriver, topNodeDriven):
	""" Connects a rig by using the rig_connectRigsFast mel command

		Args:
			topNodeDriver (str)
			topNodeDriven (str)

		Returns:
			(bool) the result of rig_connectRigsFast (int) [looks like it always returns 1]

	"""
	if not topNodeDriven or not topNodeDriver:
		raise RuntimeError("Can't connect rig when top node doesn't exist.")

	return mel.eval(
		'rig_connectRigsFast("{driven}", "{driver}");'.format(
			driven=topNodeDriven,
			driver=topNodeDriver
		)
	)