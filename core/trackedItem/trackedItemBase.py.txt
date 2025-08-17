class TrackedItem(object):
	"""objs been kept track of as a whole"""
	def __init__(self):
		# customer defined asset types in tracked items
		self.updateList = []
		self.interactiveAssetAttrs = []
	
	def getAsset(self, assetAttr):
		asset = getattr(self, assetAttr, None)
		return asset
	
	def setAsset(self, assetAttr, assetIn=None):
		if not assetAttr:
			raise RuntimeError("Can't set attribute when attribute name is empty!")
		setattr(self, assetAttr, assetIn)

	def setGatherData(self, asset, gather):
		if gather:
			asset.ifGather = True
			if asset not in self.updateList:
				self.updateList.append(asset)
		else:
			asset.ifGather = False
			if asset in self.updateList:
				self.updateList.remove(asset)

	def updateAsset(self, asset):
		"""update the asset based on the options passed from the UI
		"""
		if not asset:
			return
		if asset.ifGather:
			asset.gather()
		if asset.ifUpdate:
			asset.update()
		if asset.ifRemove:
			asset.remove()
		
	def resetFlags(self):
		for assetAttr in self.interactiveAssetAttrs:
			asset = self.getAsset(assetAttr)
			asset.ifGather = False
			asset.ifUpdate = False
			asset.ifRemove = False
		del self.updateList[:]
	
	@staticmethod
	def copyHelper(originalItem, newItem):
		"""copies the attributes of originalItem into newItem
		"""
		for assetAttr in newItem.interactiveAssetAttrs:
			asset = originalItem.getAsset(assetAttr)
			newAsset = newItem.getAsset(assetAttr)
			newAsset.ifGather = asset.ifGather
			newAsset.ifUpdate = asset.ifUpdate
			newAsset.ifRemove = asset.ifRemove
			newItem.setAsset(assetAttr, newAsset)
			if asset in originalItem.updateList:
				newItem.updateList.append(newAsset)
		return newItem