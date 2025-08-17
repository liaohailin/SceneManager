import re
import contextlib as _contextlib
from mpc.maya.mayaUtils import namespace as _namespace

from maya import cmds

from mpc import logging

_log = logging.getLogger()


@_contextlib.contextmanager
def switchNamespace(namespace):
	# Save current namespace to restore
	namespaceBeforeAction = cmds.namespaceInfo(currentNamespace=True, absoluteName=True)
	if not cmds.namespace(exists=namespace):
		cmds.namespace(add=namespace)
	cmds.namespace(setNamespace=namespace)
	try:
		yield
	finally:
		# Restore if the saved namespace still exists
		if cmds.namespace(exists=namespaceBeforeAction):
			cmds.namespace(setNamespace=namespaceBeforeAction)
		else:
			# else set namespace to root
			cmds.namespace(setNamespace=":")


def getIncrementName(name):
	textPart = ""
	numericPart = ""
	numericMatch= re.search("[0-9]*\Z", name)
	if numericMatch:
		numericPart = numericMatch.group(0)
	if numericPart:
		padding = len(numericPart)
		textPart = name.split(numericPart)[0]
		incrementedName = textPart + "{0:0{padding}d}".format(int(numericPart)+1, padding=padding)
		return incrementedName
	else:
		return name + "1"


def getRootNamespace(node):
	try:
		match = re.search("[^|:]*:", node)
	except Exception as ex:
		_log.error(ex)
	else:
		if match:
			nodeNS = match.group(0)
		else:
			_log.warning("can't find this pattern.")
	return nodeNS


def getNodeNamespace(node):
	""" Returns namespace of node

		Args:
			node (str): maya node name

		Returns:
			(str): namespace of node
	"""
	nodeNS = nodeName = ""
	try:
		match = re.search("[^|]*$", node)
	except Exception as ex:
		_log.error(ex)
	else:
		if match:
			nodeName = match.group(0)
		else:
			_log.warning("can't find this pattern.")
	try:
		match = re.search(".*:", nodeName)
	except Exception as ex:
		_log.error(ex)
	else:
		if match:
			nodeNS = match.group(0)
		else:
			_log.warning("can't find this pattern.")
	return nodeNS


def getNamespaces():
	""" Returns the namespaces of all the roots in the maya scene. """
	excludeTheseNamespaces = ("UI", "shared")
	cmds.namespace(set=':')
	allRootNamespaces = cmds.namespaceInfo(lon=True)
	
	if allRootNamespaces:
		for ns in excludeTheseNamespaces:
			if ns in allRootNamespaces:
				allRootNamespaces.remove(ns)
	
	return allRootNamespaces


def moveNamespace(sourceNamespace, targetNamespace):
	sourceNamespaceObj = _namespace.Namespace(sourceNamespace)
	targetNamespaceObj = _namespace.Namespace(targetNamespace)
	sourceNamespaceObj.move(targetNamespaceObj)
	if sourceNamespaceObj.isEmpty():
			sourceNamespaceObj.remove()


def removeNamespace(namespace, recurse=True):
	namespaceObj = _namespace.Namespace(namespace)
	if not namespaceObj.exists():
		return
	namespaceList = []
	if recurse:
		namespaceList = cmds.namespaceInfo(namespace, lon=True, recurse=True)
	namespaceList.append(namespace)
	for ns in namespaceList:
		namespaceObj = _namespace.Namespace(ns)
		if namespaceObj.isEmpty():
			namespaceObj.remove()