### start python 3 migration
from __future__ import division
from builtins import map
from builtins import str
from builtins import range
### end python 3 migration
import re

from mpc.tessa import contexts, store
from mpc import jobtools
from mpc.hub.modules.timeline import Timelines, TimelineException

from mpc.maya.animationTools.SceneManager.core import (packageUtils, shotPkg, sessionContext)
from mpc.maya.animationTools.SceneManager.core.asset import plates
from mpc.maya.animationTools.SceneManager.core.trackedItem import (trackedACP, trackedAudio, trackedCameraPkg)
from mpc.maya.animationTools.SceneManager.mayaSceneUtils import namespace, getHubSetFromScene, HubSetAsset

from maya import cmds

from Qt import QtWidgets, QtCore, QtGui
from mpc.pyPaths import mpcSharedResourcePath


from mpc.maya.animationTools.SceneManager.ui.sceneManagerUI import Ui_Form
from mpc.maya.animationTools.SceneManager.ui.tableView import ShoppingCartView
from mpc.maya.animationTools.SceneManager.ui.gatherDataModel import GatherDataModel, GatherACPDataModel
from mpc.maya.animationTools.SceneManager.ui.shoppingCartDataModel import ShoppingCartDataModel
from mpc.maya.animationTools.SceneManager.ui.updateDataModel import UpdateACPDataModel, UpdateAudioDataModel, UpdateCameraDataModel
from mpc.maya.animationTools.SceneManager.ui.customWidgets import ContextMenuHandler, CustomTabWidget
from mpc.maya.animationTools.SceneManager.ui.delegate import GatherDelegate, ACPGatherDelegate, CartDelegate, UpdateDelegate, CameraGatherDelegate
from mpc.maya.animationTools.SceneManager.ui.headerView import IconHeaderView
from mpc.maya.animationTools.assetAvailabilityCheck import check as availabilityCheck
from mpc import logging
_log = logging.getLogger()

class SceneManagerWidget(QtWidgets.QWidget, Ui_Form):
	""" Widget to create/modify a TransferMap.

		Args:
			map (TransferMap): map to be created/modified
	"""
	closed = QtCore.Signal()

	def __init__(self):
		super(SceneManagerWidget, self).__init__()

		#Setup the UI
		self.setupUi(self)

		self.setWindowTitle("Scene Manager v!VERSION!")

		styleSheetMat = mpcSharedResourcePath("animationTools", "!STYLESHEET_PATH!", "material.css")
		self.setStyleSheet(open(styleSheetMat).read())

		# signal slot dict
		self.signalSlotDict = {} 

		# ui related setting
		self.headerTab.tabBar().setVisible(False)

		# Gather header
		currentContext = contexts.fromEnvironment()
		sceneList = [scene.name for scene in currentContext.job.findScenes()] if currentContext.job else []
		shotList = [shot.name for shot in currentContext.scene.findShots()] if currentContext.scene else []

		jobName = jobtools.jobName() or ""
		sceneName = jobtools.sceneName() or ""
		shotName = jobtools.shotName() or ""
		self.manageShowPB.setText(jobName)
		self.manageScenePB.setText(sceneName)
		self.manageShotPB.setText(shotName)
		self.showLabel.setText(jobName)
		self.sceneComboBox.addItems(sceneList)
		self.sceneComboBox.setCurrentText(sceneName)
		self.shotComboBox.addItems(shotList)
		self.shotComboBox.setCurrentText(shotName)
		downArrowPath = mpcSharedResourcePath("animationTools", "!RESOURCE_INSTALL_PATH!", "img/arrowDown.png")
		downArrowStyleSheet = """
			QComboBox::down-arrow {{
				image: url({0}); /* Path to custom arrow icon */
				width: 20px;
				height: 20px;
				right: 3px;
			}}
		""".format(downArrowPath)
		self.sceneComboBox.setStyleSheet(downArrowStyleSheet)
		self.shotComboBox.setStyleSheet(downArrowStyleSheet)

		sceneCompleter = QtWidgets.QCompleter(sceneList, self.sceneComboBox)
		self.sceneComboBox.setCompleter(sceneCompleter)
		shotCompleter = QtWidgets.QCompleter(sceneList, self.shotComboBox)
		self.shotComboBox.setCompleter(shotCompleter)
		
		self.sceneComboBox.textActivated.connect(self.sceneComboUpdate)
		self.sceneComboBox.currentTextChanged.connect(self.manageScenePB.setText)
		self.sceneComboBox.currentTextChanged.connect(self.shoppingCartSceneLabel.setText)
		self.shotComboBox.textActivated.connect(self.shotComboUpdate)
		self.shotComboBox.currentTextChanged.connect(self.manageShotPB.setText)
		self.shotComboBox.currentTextChanged.connect(self.shoppingCartShotLabel.setText)

		# Manage Header
		self.refreshPushButton.clicked.connect(self.refresh)

		# tab bar
		self.setupTabBar()

		# gather tab
		self.prepareShoppingCartView()
		self.populateGatherItems()
		self.addFromBuildPB.clicked.connect(self.gatherFromBuild)
		self.addAllPB.clicked.connect(self.addAllToShoppingCart)
		self.gatherBuildPushButton.clicked.connect(self.buildScene)
		self.removeSelectedPB.clicked.connect(self.removeFromShoppingCart)
		self.shoppingCartSceneLabel.setText(sceneName)
		self.shoppingCartShotLabel.setText(shotName)

		# manage tab
		self.populateUpdateItems()
		self.updateAllPB.clicked.connect(self.updateAllInUpdateTableViews)
		self.manageApplyPushButton.clicked.connect(self.apply)

		# release tab
		self.releaseWizardPB.clicked.connect(self.openReleaseWizard)
		self.releaseWizardPB.setToolTip("to_do: merge releaseWizard to this tab")

		# set single click edit mode
		self.setSingleClickEditMode()

	@property
	def inputShow(self):
		"""Retrieve the relevant show identifier.

		Returns:
			str: A string representing the selected show.
		"""
		return self.showLabel.text()

	@property
	def inputScene(self):
		"""Retrieve the relevant scene identifier.

		Returns:
			str: A string representing the selected scene.
		"""
		return self.sceneComboBox.currentText()

	@property
	def inputShot(self):
		"""Retrieve the relevant shot identifier.

		Returns:
			str: A string representing the selected shot.
		"""
		return self.shotComboBox.currentText()

	def hasValidShot(self):
		"""Determine whether all required inputs are valid.

		Returns:
			bool: True if all required inputs are set; otherwise, False.
		"""
		return self.inputShow and self.inputScene and self.inputShot
	
	def setSingleClickEditMode(self):
		"""Triggers eidt mode on a single click on Manage Tab
		"""
		widgets = [self.acpManageTableView, self.audioManageTableView, self.cameraManageTableView]
		for tableView in widgets:
			tableView.setEditTriggers(QtWidgets.QTableView.NoEditTriggers)
		list(map(lambda tableView: tableView.clicked.connect(lambda index: tableView.edit(index)), widgets))

	def setupTabBar(self):
		self.customSceneManagerTab = CustomTabWidget()
		self.customSceneManagerTab.addTab(self.tab, "Gather")
		self.customSceneManagerTab.addTab(self.tab_2, "Manage")
		self.customSceneManagerTab.addTab(self.tab_3, "Release")
		self.verticalLayout.insertWidget(1, self.customSceneManagerTab)
		self.sceneManagerTab.deleteLater()
		self.tabSwitch(self.customSceneManagerTab.currentIndex())
		self.customSceneManagerTab.currentChanged.connect(self.tabSwitch)

	def tabSwitch(self, tabIndex):
		self.headerTab.setCurrentIndex(tabIndex)

	def closeEvent(self, event):
		QtWidgets.QWidget.closeEvent(self, event)
		self.closed.emit()
	
	def sceneComboUpdate(self, newSceneText):
		scene = contexts.Scene(self.inputShow, newSceneText)
		shotList = [shot.name for shot in scene.findShots()]
		shotList.insert(0, "")

		self.shotComboBox.clear()
		self.shotComboBox.addItems(shotList)
		self.shotComboBox.setCurrentText("")

		shotCompleter = QtWidgets.QCompleter(shotList, self.shotComboBox)
		self.shotComboBox.setCompleter(shotCompleter)

	def shotComboUpdate(self, newShotText):
		if newShotText:
			self.populateGatherItems()
	
	def openReleaseWizard(self):
		from mpc.maya.animationTools.dockTools.releaseWizardTool.app import releaseWizardMaya
		releaseWizardMaya.ReleaseWizardMaya.showUI(nonDisruptive=True)

	def gatherFromBuild(self):
		from mpc.maya.animationTools.ACPManager.widgets.rigGatherWidgets import RigGatherDialog
		dialog = RigGatherDialog()
		dialog.show()
		result = dialog.exec_()
		if not result:
			return
		assetSelected = dialog.getAssetSelected()
		if not assetSelected:
			return
		gatherType = dialog.getGatherType()
		numInstances = dialog.getNumInstances()
		for i in range(1, numInstances + 1):
			trackedCP = trackedACP.GatherACP(assetSelected.name, hubElement=assetSelected.name, tessaAsset=assetSelected, cp=True)
			if gatherType == "rigPuppet":
				trackedCP.setGatherData(trackedCP.getAsset("highBodyRigPuppet"), True)
			elif gatherType == "lowResRigPuppet":
				trackedCP.setGatherData(trackedCP.getAsset("lowBodyRigPuppet"), True)
			elif gatherType == "facialRigPuppet":
				trackedCP.setGatherData(trackedCP.getAsset("highFaceRigPuppet"), True)
			elif gatherType == "lowFacialRigPuppet":
				trackedCP.setGatherData(trackedCP.getAsset("lowFaceRigPuppet"), True)
			elif gatherType == "facialAndBodyRigPuppet":
				trackedCP.setGatherData(trackedCP.getAsset("highBodyRigPuppet"), True)
				trackedCP.setGatherData(trackedCP.getAsset("highFaceRigPuppet"), True)
			elif gatherType == "facialAndLowResBodyRigPuppet":
				trackedCP.setGatherData(trackedCP.getAsset("lowBodyRigPuppet"), True)
				trackedCP.setGatherData(trackedCP.getAsset("highFaceRigPuppet"), True)
			elif gatherType == "lowFacialAndHighBodyRigPuppet":
				trackedCP.setGatherData(trackedCP.getAsset("highBodyRigPuppet"), True)
				trackedCP.setGatherData(trackedCP.getAsset("lowFaceRigPuppet"), True)
			elif gatherType == "lowFacialAndLowResBodyRigPuppet":
				trackedCP.setGatherData(trackedCP.getAsset("lowBodyRigPuppet"), True)
				trackedCP.setGatherData(trackedCP.getAsset("lowFaceRigPuppet"), True)
			self.shoppingCartModel.updateItem(trackedCP)

	def prepareShoppingCartView(self):
		self.shoppingCartModel = ShoppingCartDataModel(data=[trackedACP.GatherACP("initObj")], header=["Name", "Shot"])
		self.shoppingCartModel.itemAdded.connect(self.resizeShoppingCartView)
		self.customShoppingCartView = ShoppingCartView(inputTableView=self.shoppingCartView)
		# replace shoppingCartView with customShoppingCartView
		self.shoppingCartGroup.layout().removeWidget(self.shoppingCartView)
		self.shoppingCartView.deleteLater()
		self.shoppingCartGroup.layout().insertWidget(1, self.customShoppingCartView)
		self.customShoppingCartView.setModel(self.shoppingCartModel)
		self.customShoppingCartView.setItemDelegate(CartDelegate(self.customShoppingCartView, self.shoppingCartModel))

	def resizeShoppingCartView(self):
		self.customShoppingCartView.resizeColumnsToContents()

	def addAllToShoppingCart(self):		
		trackedItems = []
		for dataModelAttrGroup in [
			("gatherACPModel", [1,3,5,6]),
			("gatherAudioModel", [1]),
			("gatherCameraModel", [1, 2])
		]:
			dataModelAttr, selectColumnList = dataModelAttrGroup
			dataModel = getattr(self, dataModelAttr, None)
			if dataModel:
				for row in range(dataModel.rowCount()):
					for column in selectColumnList:
						dataModel.setGatherData(dataModel.index(row, column), True)
					trackedItems.append(dataModel.trackedItem(dataModel.index(row, 0)))
		for item in trackedItems:
			self.shoppingCartModel.updateItem(item)

	def removeFromShoppingCart(self):
		itemsToRemove = [self.shoppingCartModel.trackedItem(index) for index in self.customShoppingCartView.selectionModel().selectedRows(column=0)]
		self.removeItemsFromShoppingCart(itemsToRemove)

	def removeItemsFromShoppingCart(self, itemsToRemove):
		"""send trackedItems to remove from shopping cart
		args:
			itemsToRemove(list of TrackedItem):
		"""
		for item in itemsToRemove:
			for attr in item.interactiveAssetAttrs:
				item.setGatherData(item.getAsset(attr), False)
			self.shoppingCartModel.removeItem(item)
		# update other data model after remove
		for dataModelAttr in ["gatherACPModel", "gatherAudioModel", "gatherCameraModel"]:
			dataModel = getattr(self, dataModelAttr, None)
			if dataModel:
				firstIndex = dataModel.index(0,0)
				lastIndex = dataModel.index(dataModel.rowCount(),dataModel.columnCount())
				dataModel.dataChanged.emit(firstIndex, lastIndex, [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole])

	def updateAllInUpdateTableViews(self):
		"""Update all the items on the Manage tab to the latest version
		"""
		#TODO: this method needs to be refactored, there is some repeating code
		if hasattr(self, "updateACPModel"):
			for row in range(self.updateACPModel.rowCount()):
				for column in range(self.updateACPModel.columnCount()):
					# do not update animation curve automatically
					# TODO: replace this hardcode stuff with better solution
					if column in [0, 5, 6]:
						continue
					index = self.updateACPModel.index(row, column)
					asset = self.updateACPModel.asset(index)
					if self.updateACPModel.isAssetValid(asset) and self.updateACPModel.assetOutDated(asset):
						self.updateACPModel.setUpdateData(index, list(asset.assetVersions)[0])
		if hasattr(self, "updateAudioDataModel"):
			for row in range(self.updateAudioDataModel.rowCount()):
				for column in range(self.updateAudioDataModel.columnCount()):
					if column > 0:
						index = self.updateAudioDataModel.index(row, column)
						asset = self.updateAudioDataModel.asset(index)
						if self.updateAudioDataModel.isAssetValid(asset) and self.updateAudioDataModel.assetOutDated(asset):
							self.updateAudioDataModel.setUpdateData(index, list(asset.assetVersions)[0])
		if hasattr(self, "updateCameraDataModel"):
			for row in range(self.updateCameraDataModel.rowCount()):
				for column in range(self.updateCameraDataModel.columnCount()):
					if column > 0:
						index = self.updateCameraDataModel.index(row, column)
						asset = self.updateCameraDataModel.asset(index)
						if self.updateCameraDataModel.isAssetValid(asset) and self.updateCameraDataModel.assetOutDated(asset):
							self.updateCameraDataModel.setUpdateData(index, list(asset.assetVersions)[0])

	def populateGatherItems(self):
		if not self.hasValidShot():
			_log.info("Does not have a valid shot context. Skip populating gather items.")
			return
		context = sessionContext.SessionContext(
			shot=contexts.Shot(self.inputShow, self.inputScene, self.inputShot)
		)
		shotPkgObj = shotPkg.ShotPkg(context)

		# update header frame range according to current context
		try:
			timeline = Timelines.getTimelineDicts(
				context.job, context.scene, context.shot)['work']
		except (KeyError, TimelineException):
			self.gatherHeadHandlePB.setText("")
			self.gatherFrameRangeButton.setText("No Valid Frame Range")
			self.gatherTailHandlePB.setText("")
		else:
			self.gatherHeadHandlePB.setText(str(int(timeline["workStart"])))
			self.gatherFrameRangeButton.setText("{0}-{1}".format(timeline["cutStart"], timeline["cutEnd"]))
			self.gatherTailHandlePB.setText(str(int(timeline["workEnd"])))

		# populate gatherable items to tableview
		gatherItems = []
		assetType = "AnimatedCharacterPkg"
		if self.sceneComboBox.currentText() == "build":
			assetType = "CharacterPkg"
			cpAssets = store.findAssets(context.tessaContext, assetType=assetType)
			cpAssetVersionList = [cpAsset.gather(store.vLatest) for cpAsset in cpAssets if context.stream == cpAsset.stream.name]
			for cpAssetVersion in cpAssetVersionList:
				trackedCP = trackedACP.GatherACP(cpAssetVersion.name, hubElement=cpAssetVersion.name, tessaAsset=cpAssetVersion, cp=True)
				gatherItems.append(trackedCP)
		else:
			if shotPkgObj.shotPkg:
				for acp in shotPkgObj.acpList:
					trackedCP = trackedACP.GatherACP(acp.name, hubElement=acp.name, tessaAsset=acp, cp=False)
					gatherItems.append(trackedCP)
			else:
				cpAssets = store.findAssets(context.tessaContext, assetType=assetType)
				cpAssetVersionList = [cpAsset.gather(store.vLatest) for cpAsset in cpAssets if context.stream == cpAsset.stream.name]
				for cpAssetVersion in cpAssetVersionList:
					trackedCP = trackedACP.GatherACP(cpAssetVersion.name, hubElement=cpAssetVersion.name, tessaAsset=cpAssetVersion, cp=False)
					gatherItems.append(trackedCP)
		if gatherItems:
			if not getattr(self, "gatherACPModel", None):
				# scan scene and see if there is already rig existed
				self.gatherACPModel = GatherACPDataModel(gatherItems, gatherItems[0].interactiveAssetAttrs, shotPkg=shotPkgObj)
				self.acpGatherTableView.setModel(self.gatherACPModel)
				#self.acpGatherTableView.verticalHeader().setVisible(False)
				self.acpGatherTableView.setHorizontalHeader(IconHeaderView(parent=self.acpGatherTableView))
				self.gatherACPDelegate = ACPGatherDelegate(self.acpGatherTableView, self.gatherACPModel, self.shoppingCartModel)
				self.acpGatherTableView.setItemDelegate(self.gatherACPDelegate)
			else:
				self.gatherACPModel.resetData(data=gatherItems, header=gatherItems[0].interactiveAssetAttrs, shotPkg=shotPkgObj)
		else:
			if getattr(self, "gatherACPModel", None):
				placeHolder = trackedACP.GatherACP("noValidACP/CP")
				self.gatherACPModel.resetData(data=[placeHolder], header=placeHolder.interactiveAssetAttrs, shotPkg=shotPkgObj)
		
		# populating audio table
		trackedAudios = []
		audioAsset = shotPkgObj.audioAsset
		if audioAsset:
			trackedAudios.append(trackedAudio.TrackedAudio(audioAsset.name, tessaAsset=audioAsset))
		else:
			for shotAudio in store.findAssets(context.tessaContext, assetType="audio"):
				if audioAsset and shotAudio.name == "masterAudio":
					latestShotAudio = shotAudio.gather(store.vLatest)
					trackedAudios.append(trackedAudio.TrackedAudio(shotAudio.name, tessaAsset=latestShotAudio))
		if trackedAudios:
			if not getattr(self, "gatherAudioModel", None):
				# just reuse the GatherDataModel
				self.gatherAudioModel = GatherDataModel(trackedAudios, ["Name"]+trackedAudios[0].interactiveAssetAttrs)
				self.audioGatherTableView.setModel(self.gatherAudioModel)
				#self.audioGatherTableView.setHorizontalHeader(IconHeaderView(parent=self.audioGatherTableView))
				self.audioGatherTableView.setItemDelegate(GatherDelegate(self.audioGatherTableView, self.gatherAudioModel, self.shoppingCartModel, activeColor=QtGui.QColor("#F3CE5E")))
			else:
				self.gatherAudioModel.resetData(data=trackedAudios, header=["Name"]+trackedAudios[0].interactiveAssetAttrs)
		else:
			if getattr(self, "gatherAudioModel", None):
				placeHolder = trackedAudio.TrackedAudio("noValidAudio")
				self.gatherAudioModel.resetData(data=[placeHolder], header=["Name"]+placeHolder.interactiveAssetAttrs)
		
		trackedCameras = []
		if shotPkgObj.cameraPkg:
			trackedCameras.append(trackedCameraPkg.GatherCameraPkg(shotPkgObj.cameraPkg.name, tessaAsset=shotPkgObj.cameraPkg))
		
		for camera in packageUtils.CameraRepository.generator(context.tessaContext):
			if shotPkgObj.cameraPkg and shotPkgObj.cameraPkg.name == camera.name:
				continue
			trackedCameras.append(trackedCameraPkg.GatherCameraPkg(camera.name, tessaAsset=camera))
		if trackedCameras:
			if not getattr(self, "gatherCameraModel", None):
				# just reuse the GatherDataModel
				self.gatherCameraModel = GatherDataModel(trackedCameras, trackedCameras[0].interactiveAssetAttrs)
				self.cameraGatherTableView.setModel(self.gatherCameraModel)
				self.cameraGatherTableView.setHorizontalHeader(IconHeaderView(activeColor=QtGui.QColor("#C5DA83"), parent=self.cameraGatherTableView))
				self.cameraGatherTableView.setItemDelegate(CameraGatherDelegate(self.cameraGatherTableView, self.gatherCameraModel, self.shoppingCartModel, activeColor=QtGui.QColor("#C5DA83")))
			else:
				self.gatherCameraModel.resetData(data=trackedCameras, header=trackedCameras[0].interactiveAssetAttrs)
		else:
			if getattr(self, "gatherCameraModel", None):
				placeHolder = trackedCameraPkg.GatherCameraPkg("noValidCamera")
				self.gatherCameraModel.resetData(data=[placeHolder], header=placeHolder.interactiveAssetAttrs)

	def updateFrameRange(self, timeline):
		if timeline:
			cmds.playbackOptions(edit=True, minTime=timeline["workStart"])
			cmds.playbackOptions(edit=True, maxTime=timeline["workEnd"])
			cmds.playbackOptions(edit=True, animationStartTime=timeline["workStart"])
			cmds.playbackOptions(edit=True, animationEndTime=timeline["workEnd"])
			self.updateFrameRangeButton.setText("{0}-{1}".format(timeline["cutStart"], timeline["cutEnd"]))
			self.updateHeadHandlePB.setStyleSheet("background-color : #C5DA83")
			self.updateTailHandlePB.setStyleSheet("background-color : #C5DA83")

	def refresh(self):
		self.populateUpdateItems()
		# refresh apply button back to its origin color
		self.manageApplyPushButton.setStyleSheet("background-color: #636466;")

	def apply(self):
		self.updateScene()
		# set apply button back to its origin color after operation finished
		self.manageApplyPushButton.setStyleSheet("background-color: #636466;")

	def populateUpdateItems(self):
		if not self.hasValidShot():
			_log.info("Does not have a valid shot context. Skip populating update items.")
			return

		context =  sessionContext.SessionContext(
			shot=contexts.Shot(self.inputShow, self.inputScene, self.inputShot)
		)
		currentShotPkg = shotPkg.ShotPkg(context)

		try:
			timeline = Timelines.getTimelineDicts(
				context.job, context.scene, context.shot)['work']
		except (KeyError, TimelineException):
			self.updateHeadHandlePB.setText("")
			self.updateFrameRangeButton.setText("No Valid Frame Range")
			self.updateTailHandlePB.setText("")
		else:
			startTime = cmds.playbackOptions(query=True, minTime=True)
			endTime = cmds.playbackOptions(query=True, maxTime=True)
			animStartTime = cmds.playbackOptions(query=True, animationStartTime=True)
			animEndTime = cmds.playbackOptions(query=True, animationEndTime=True)
			if startTime != timeline["workStart"] or endTime != timeline["workEnd"] or \
			animStartTime != timeline["workStart"] or animEndTime != timeline["workEnd"]:
				self.updateFrameRangeButton.setText("update to {0}-{1}".format(
					int(timeline["workStart"]), int(timeline["workEnd"]))
				)
				self.updateHeadHandlePB.setStyleSheet("background-color : #EF4A3E")
				self.updateTailHandlePB.setStyleSheet("background-color : #EF4A3E")
				existedSlot = self.signalSlotDict.get(self.updateFrameRangeButton.clicked)
				if existedSlot:
					self.updateFrameRangeButton.clicked.disconnect(existedSlot)
				self.updateFrameRangeButton.clicked.connect(
					lambda: self.updateFrameRange(timeline)
				)
				self.signalSlotDict[self.updateFrameRangeButton.clicked] = self.updateFrameRange
			else:
				self.updateFrameRangeButton.setText("{0}-{1}".format(int(timeline["cutStart"]), int(timeline["cutEnd"])))
			self.updateHeadHandlePB.setText(str(int(timeline["workStart"])))
			self.updateTailHandlePB.setText(str(int(timeline["workEnd"])))

		# populate update items
		allNamespaces = namespace.getNamespaces()
		updateItems = []
		for n in allNamespaces:
			if re.match("[a-z0-9A-Z]*[0-9][0-9][0-9][0-9]\Z", n):
				sceneACP = trackedACP.UpdateACP(n, cp=False)
			else:
				sceneACP = trackedACP.UpdateACP(n, cp=True)
			if sceneACP.hasValidAsset():
				updateItems.append(sceneACP)
		if updateItems:
			if not getattr(self, "updateACPModel", None):
				# manage tab has the data model one can manage
				self.updateACPModel = UpdateACPDataModel(updateItems, updateItems[0].interactiveAssetAttrs, shotPkg=currentShotPkg)
				self.updateACPModel.userEdited.connect(self.userEdited)
				self.acpManageTableView.setModel(self.updateACPModel)
				self.acpManageTableView.setHorizontalHeader(IconHeaderView(parent=self.acpManageTableView))
				self.acpManageTableView.setItemDelegate(UpdateDelegate(self.acpManageTableView, self.updateACPModel))
				# set promote handler
				self.promoteHandler = ContextMenuHandler(parent=self.acpManageTableView)
				self.acpManageTableView.installEventFilter(self.promoteHandler)
			else:
				self.updateACPModel.resetData(
					data=updateItems, header=updateItems[0].interactiveAssetAttrs, shotPkg=currentShotPkg
				)

		#populate camera update items
		cameraUpdateItems = []
		for cameraHubset in getHubSetFromScene({"hubBundle": "CameraPkg"}):
			hubsetAsset = HubSetAsset(cameraHubset)
			cameraTessaAsset = hubsetAsset.tessaAsset
			if cameraTessaAsset:
				cameraUpdateItems.append(trackedCameraPkg.UpdateCameraPkg(cameraTessaAsset.name, tessaAsset=cameraTessaAsset))
		if cameraUpdateItems:
			if not getattr(self, "updateCameraDataModel", None):
				self.updateCameraDataModel = UpdateCameraDataModel(cameraUpdateItems, cameraUpdateItems[0].interactiveAssetAttrs, shotPkg=currentShotPkg)
				self.updateCameraDataModel.userEdited.connect(self.userEdited)
				self.cameraManageTableView.setModel(self.updateCameraDataModel)
				self.cameraManageTableView.setHorizontalHeader(IconHeaderView(activeColor=QtGui.QColor("#C5DA83"), parent=self.cameraManageTableView))
				self.cameraManageTableView.setItemDelegate(UpdateDelegate(self.cameraManageTableView, self.updateCameraDataModel))
			else:
				self.updateCameraDataModel.resetData(data=cameraUpdateItems, header=cameraUpdateItems[0].interactiveAssetAttrs, shotPkg=currentShotPkg)

		# populate audio update items
		audioUpdateItems = []
		for audioHubset in getHubSetFromScene({"hubBundle": "audio"}):
			hubsetAsset = HubSetAsset(audioHubset)
			audioTessaAssset = hubsetAsset.tessaAsset
			if audioTessaAssset:
				audioUpdateItems.append(trackedAudio.UpdateAudio(audioTessaAssset.name, tessaAsset=audioTessaAssset))
		
		if audioUpdateItems:
			if not getattr(self, "updateAudioDataModel", None):
				self.updateAudioDataModel = UpdateAudioDataModel(audioUpdateItems, audioUpdateItems[0].interactiveAssetAttrs, shotPkg=currentShotPkg)
				self.updateAudioDataModel.userEdited.connect(self.userEdited)
				self.audioManageTableView.setModel(self.updateAudioDataModel)
				self.audioManageTableView.setHorizontalHeader(IconHeaderView(activeColor=QtGui.QColor("#F3CE5E"), parent=self.audioManageTableView))
				self.audioManageTableView.setItemDelegate(UpdateDelegate(self.audioManageTableView, self.updateAudioDataModel))
			else:
				self.updateAudioDataModel.resetData(data=audioUpdateItems, header=audioUpdateItems[0].interactiveAssetAttrs, shotPkg=currentShotPkg)

		if updateItems or cameraUpdateItems or audioUpdateItems:
			self.customSceneManagerTab.setCurrentIndex(1)
		else:
			self.customSceneManagerTab.setCurrentIndex(0)

	def availabilityCheck(self, trackedItemList):
		# check availability
		assetTrackedItemDict = {}
		assetSyncResultDict = {}
		syncPaths = []
		for trackedItem in trackedItemList:
			for assetAttr in trackedItem.interactiveAssetAttrs:
				asset = trackedItem.getAsset(assetAttr)
				if asset and asset.tessaAsset and (asset.ifGather or asset.ifUpdate):
					if asset.tessaAsset not in assetTrackedItemDict:
						assetTrackedItemDict[asset.tessaAsset] = []
					assetTrackedItemDict[asset.tessaAsset].append(trackedItem)
		for tessaAsset in assetTrackedItemDict:
			if isinstance(tessaAsset, plates.PlatesTessaAsset):
				syncResults = []
				for asset in tessaAsset.assets:
					syncResult, assetPaths = availabilityCheck.isAssetAvailable(asset)
					syncPaths.extend(assetPaths)
					syncResults.append(syncResult)
				assetSyncResultDict[tessaAsset] = all(syncResults)
			else:
				syncResult, assetPaths = availabilityCheck.isAssetAvailable(tessaAsset)
				syncPaths.extend(assetPaths)
				assetSyncResultDict[tessaAsset] = syncResult

		if syncPaths:
			self.syncDialogue = availabilityCheck.syncPaths(syncPaths)
			self.syncDialogue.show()

		syncingList = []
		for tessaAsset in assetTrackedItemDict:
			if not assetSyncResultDict[tessaAsset]:
				syncingList.extend(assetTrackedItemDict[tessaAsset])
		return list(set(syncingList))

	def buildScene(self):
		# check availability
		syncingList = self.availabilityCheck(self.shoppingCartModel.dataList)
		gatherList = list(set(self.shoppingCartModel.dataList) - set(syncingList))
		for cartItem in gatherList:
			copiedItem = cartItem.copy(cartItem)
			copiedItem.processAssets()
		#remove whatever has been gathered from shopping cart
		self.removeItemsFromShoppingCart(gatherList)
		# repopulate gather tab and update tab after gather
		self.populateUpdateItems()
	
	def updateScene(self):
		if hasattr(self, "updateACPModel"):
			while(self.updateACPModel.dataRemoveList):
				acp = self.updateACPModel.dataRemoveList.pop()
				#remove assets
				acp.processAssets()
				#remove namespace
				namespace.removeNamespace(acp.trackedItemName)
			
			# check availability
			syncingList = self.availabilityCheck(self.updateACPModel.dataList)
			updateList = list(set(self.updateACPModel.dataList)-set(syncingList))
			for trackedACP in updateList:
				trackedACP.processAssets()

		if hasattr(self, "updateAudioDataModel"):
			while(self.updateAudioDataModel.dataRemoveList):
				audio = self.updateAudioDataModel.dataRemoveList.pop()
				#remove asset
				audio.processAssets()
				#remove namespace
				namespace.removeNamespace(audio.trackedItemName)

			# check availability
			syncingList = self.availabilityCheck(self.updateAudioDataModel.dataList)
			updateList = list(set(self.updateAudioDataModel.dataList) - set(syncingList))
			for trackedAudio in updateList:
				trackedAudio.processAssets()

		if hasattr(self, "updateCameraDataModel"):
			while(self.updateCameraDataModel.dataRemoveList):
				camera = self.updateCameraDataModel.dataRemoveList.pop()
				camera.processAssets()
				namespace.removeNamespace(camera.trackedItemName)
		
			syncingList = self.availabilityCheck(self.updateCameraDataModel.dataList)
			updateList = list(set(self.updateCameraDataModel.dataList) - set(syncingList))
			for trackedCamera in updateList:
				trackedCamera.processAssets()
	
	def userEdited(self):
		# make apply button red when data changed
		self.manageApplyPushButton.setStyleSheet("background-color: #EF4A3E;")