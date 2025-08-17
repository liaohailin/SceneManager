"""Deal with hubset in maya scene to get hubset info and top nodes of wanted assets
"""
### start python 3 migration
from builtins import zip
from builtins import filter
from builtins import str
from functools import reduce
### end python 3 migration

from mpc import jobtools

from mpc.tessa import contexts, legacy, store, uri
from mpc.tessa import exceptions as tessaExceptions

import re

from maya import cmds

from mpc import logging
_log = logging.getLogger()


class HubSetAsset(object):
	""" A hubset class to make it easier to access attributes of hubset.
		This also contains the tessa asset 
	"""

	def __init__(self, hubSet):
		"""	Args:
				hubset (string): Name of the maya set
			
			Kwargs:
				silent(bool): if false, the object will print warnings
		"""
		self.name = hubSet
		setInfo = dict(list(zip(("job", "scene", "shot", "bundle", "element", "version", "prefix", "stream"),
			getAssetDataFromHubSet(hubSet))))
		for key, value in setInfo.items():
			setattr(self, key, value)

		# Check for broken hubSet
		if not self.element:
			raise AttributeError("Element name is invalid for hubset {}".format(hubSet))

		self.tessaAsset = self._getTessaAsset()
		try:
			self.nextVersion = int(self.tessaAsset.version) + 1
		except AttributeError:
			self.nextVersion = 1

	def _getTessaAsset(self):
		""" Gets the tessa asset with the hub info

			Return: 
				(Tessa Asset or Tessa AssetVersion): If the asset exists in Tessa, 
					AssetVersion is returned. Otherwise, returns a Tessa Asset.
		"""
		context = contexts.Shot(self.job, self.scene, self.shot)
		# if asset does not exist, it may be a new asset.
		# return an asset with no version 
		assetVersion = None
		gatherVersion = None
		if self.version:
			gatherVersion = self.version
		else:
			gatherVersion = store.vLatest

		assetName = self.element
		if self.bundle == "animCurves":
			assetName = "{0}_{1}".format(self.prefix, self.element)
		elif self.bundle == "CharacterPkg":
			if not self.stream:
				self.stream = "anim"
	
		try:
			assetVersion = store.Asset(context, self.bundle, assetName, stream=self.stream).gather(gatherVersion)
		except tessaExceptions.AssetNotFound:
			 _log.warning("can't get designated asset {0}:{1}".format(self.bundle, assetName))

		return assetVersion


def getAssetDataFromHubSet(hubSet):
	""" Retrieves data from the hubSet
	
		Args:
			hubSet (str): name of the hubset to retrieve data from

		Returns:
			(job, scene, shot, bundle, element, version, prefix, stream, rigPuppet): data retrieved from the hubset 
	"""
	job = jobtools.jobName()
	scene = None
	shot = None
	bundle = None
	element = None
	stream = None
	version = None
	rigPuppet = None # Which is, in fact, the rigPuppet's topGrp

	if cmds.attributeQuery("hubScene", node=hubSet, exists=True) and cmds.attributeQuery("hubShot", node=hubSet, exists=True):
		scene = cmds.getAttr("{}.hubScene".format(hubSet))
		shot = cmds.getAttr("{}.hubShot".format(hubSet))
	elif cmds.attributeQuery("hubSceneShot", node=hubSet, exists=True):
		sceneShot = cmds.getAttr("{}.hubSceneShot".format(hubSet)).split('/')
		scene = sceneShot[0]
		shot = sceneShot[1]

	if cmds.attributeQuery("hubBundle", node=hubSet, exists=True):
		bundle = str(cmds.getAttr("{}.hubBundle".format(hubSet)))

	if cmds.attributeQuery("hubElement", node=hubSet, exists=True):
		element = str(cmds.getAttr("{}.hubElement".format(hubSet)))

	if cmds.attributeQuery("version", node=hubSet, exists=True):
		version = str(cmds.getAttr("{}.version".format(hubSet)))

	prefix = None
	if cmds.attributeQuery("hubPrefix", node=hubSet, exists=True):
		prefix = str(cmds.getAttr("{}.hubPrefix".format(hubSet)))

	if cmds.attributeQuery("stream", node=hubSet, exists=True)\
			and cmds.getAttr("{}.stream".format(hubSet)) != "None"\
			and cmds.getAttr("{}.stream".format(hubSet)):
		stream = cmds.getAttr("{}.stream".format(hubSet))

	if cmds.attributeQuery("rigPuppet", node=hubSet, exists=True):
		rigPuppet = cmds.listConnections("{}.rigPuppet".format(hubSet), source=True, destination=False)[0]

	if re.match("^v-?[0-9]+$", version):
		version = int(version.strip('v'))
	else:
		version = None

	return job, scene, shot, bundle, element, version, prefix, stream, rigPuppet


def filterByName(name, setList=[]):
	""" Returns list of sets that start with name
		Args:
			name (str): start string of a set name
			setList (list of str): giving a list of sets to filter
	"""
	outputSetList = []
	for set in setList:
		if set.startswith(name):
			outputSetList.append(set)
	return outputSetList


def filterByAttributes(attrDict, seq):
	""" Returns list of elements from seq that have attributes as specified by attrDict

		Args:
			attrDict (dict): a dictionary of pairs (attrName, attrValue)
			seq (iterable): sequence of maya nodes

		Returns:
			(list): elements from sequence having correct attributes
	"""
	if not seq:
		return None

	ffilter = lambda item: (
		reduce(
			lambda res, attrPair: (
				res and
				cmds.attributeQuery(attrPair[0], node=item, exists=True) and
				cmds.getAttr('.'.join([item, attrPair[0]])) == attrPair[1]
			),
			iter(list(attrDict.items())),
			True
		)
	)

	return list(filter(ffilter, seq))


def getHubSetFromScene(setInfo, startName="", setList=[]):
	""" Returns list of objectSets in the maya scene that have correct name or attributes

		Args:
			setInfo (str or dict): if typeof(setInfo) == str => the objectSet named as setInfo
									if typeof(setInfo) == dict => attributes that the objectSet must have
			setList (list of str): giving a list of sets so can limit search range

		Returns:
			(List): objectSets in the maya scene that have correct name or attributes
	"""
	if isinstance(setInfo, str):
		if cmds.objExists(setInfo):
			return [setInfo]
		return None
	if not setList:
		setList = cmds.ls(l=1, sets=1)
	if startName:
		setList = filterByName(startName, setList)
	sets = filterByAttributes(setInfo, setList)

	return sets


def getInfoForHubSet(set):
	""" Returns a dictionary of pairs (hubAttrName, attrValue) for the hub set

		Args:
			set (str): name of an existing hub objectSet

		Returns:
			setInfo (dict): a dictionary of pairs (hubAttrName, attrValue) for the hub set
	"""
	setInfo = {}

	setInfo["setName"] = set
	attrs = ["hubPrefix", "hubScene", "hubShot", "hubBundle", "hubElement", "version"]
	for attr in attrs:
		if cmds.attributeQuery(attr, node=set, exists=True):
			setInfo[attr] = cmds.getAttr('.'.join([set, attr]))
		else:
			setInfo[attr] = ''

	return setInfo


def getTopNodeFromSet(set, connectionName):
	""" Returns top node in the set linked to it using connectionName

		Args:
			set (str): name of an existing hub objectSet
			connectionName (str): connection name for the node

		Returns:
			topNode (str): name of the top node that belogs to the set and is linked to it using connectionName
	"""
	if not set:
		return ""

	ffilter = lambda item: (
		cmds.attributeQuery(connectionName, node=item, exists=True) and
		cmds.listConnections('.'.join([item, connectionName]))[0] == set
	)
	try:
		topNode = list(filter(ffilter, cmds.sets(set, q=1)))
	except ValueError:
		return ""

	if len(topNode) != 1:
		return ""

	return topNode[0]


def addToSet(setName, nodesNames):
	"""Add given nodes to the given set.

	Args:
		setName (str): Set we want to add the given nodes to.
		nodesNames (list[str]): Nodes we want to add to the given set.
	"""
	cmds.sets(nodesNames, edit=True, addElement=setName)


def getParentSet(filterfunc, node):
	""" BFS is performed to search recursively for the first parent set
		that contains node and satisfies the condition specified by filterfunc

		Args:
			filterfunc (predicate): a function taking one arg of type objectSet and returns true or false
			node (str): maya node to start the search from

		Returns:
			objectsSet (str): The parent objectSet that contains node and satisfies the condition
				specified by filterfunc.
	"""
	psets = None
	if cmds.nodeType(node) == "objectSet":
		psets = [node]
	else:
		psets = cmds.listSets(o=node)

	if not psets:
		return None

	while len(psets) > 0:
		node = psets[0]
		psets = psets[1:]
		if filterfunc(node):
			return node

		parentsets = cmds.listSets(o=node)
		if parentsets is not None:
			psets.extend(parentsets)

	return None