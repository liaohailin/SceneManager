from Qt import QtCore, QtWidgets, QtGui
from mpc.pyPaths import mpcSharedResourcePath
from mpc.maya.animationTools.SceneManager.ui import qtUtils


class ShoppingCartView(QtWidgets.QTableView):

	def __init__(self, inputTableView=None):
		"""
		arg:
		inputTableView(QTableView): gonna copy whatever settings from input table view
		"""
		super(ShoppingCartView, self).__init__()
		if inputTableView:
			self.copyInputTableViewSettings(inputTableView)

	def paintEvent(self, event):
		painter = QtGui.QPainter(self.viewport())
		pixmapRect = QtCore.QRect(self.rect().x(), self.rect().y()+self.rect().height()-self.rect().width(), self.rect().width(), self.rect().width())
		pixmapRect = qtUtils.addPaddingToRect(pixmapRect, 50)
		backgroundImagePath = mpcSharedResourcePath(u"animationTools", u"!RESOURCE_INSTALL_PATH!", u"img/sceneManager/SM_icon_basket.svg")
		backgroundImage = qtUtils.getColoredPixmap(backgroundImagePath, "#636466", pixmapRect.width(), pixmapRect.height())
		painter.drawPixmap(pixmapRect, backgroundImage)
		super(ShoppingCartView, self).paintEvent(event)

	def copyInputTableViewSettings(self, inputTableView):
		# Copy position and size
		self.setGeometry(inputTableView.geometry())
		# Copy general settings
		self.setSelectionMode(inputTableView.selectionMode())
		self.setSelectionBehavior(inputTableView.selectionBehavior())
		self.setShowGrid(inputTableView.showGrid())
		self.setGridStyle(inputTableView.gridStyle())
		self.setWordWrap(inputTableView.wordWrap())
		self.setAlternatingRowColors(inputTableView.alternatingRowColors())
		self.setVerticalScrollMode(inputTableView.verticalScrollMode())
		self.setHorizontalScrollMode(inputTableView.horizontalScrollMode())
		self.setSortingEnabled(inputTableView.isSortingEnabled())
		self.setEditTriggers(inputTableView.editTriggers())
		self.setIconSize(inputTableView.iconSize())
		self.setTextElideMode(inputTableView.textElideMode())
		self.setDragEnabled(inputTableView.dragEnabled())
		self.setAcceptDrops(inputTableView.acceptDrops())
		self.setDragDropOverwriteMode(inputTableView.dragDropOverwriteMode())
		self.setDragDropMode(inputTableView.dragDropMode())
		self.setDropIndicatorShown(inputTableView.showDropIndicator())
		self.setDefaultDropAction(inputTableView.defaultDropAction())
		
		# Copy header settings
		self.horizontalHeader().setStretchLastSection(inputTableView.horizontalHeader().stretchLastSection())
		self.horizontalHeader().setDefaultSectionSize(inputTableView.horizontalHeader().defaultSectionSize())
		self.horizontalHeader().setMinimumSectionSize(inputTableView.horizontalHeader().minimumSectionSize())
		self.horizontalHeader().setHighlightSections(inputTableView.horizontalHeader().highlightSections())
		self.horizontalHeader().setSectionsClickable(inputTableView.horizontalHeader().sectionsClickable())
		self.horizontalHeader().setSectionsMovable(inputTableView.horizontalHeader().sectionsMovable())
		
		# Copy vertical header settings
		self.verticalHeader().setVisible(inputTableView.verticalHeader().isVisible())
		self.verticalHeader().setDefaultSectionSize(inputTableView.verticalHeader().defaultSectionSize())
		self.verticalHeader().setMinimumSectionSize(inputTableView.verticalHeader().minimumSectionSize())
		self.verticalHeader().setHighlightSections(inputTableView.verticalHeader().highlightSections())
		self.verticalHeader().setSectionsClickable(inputTableView.verticalHeader().sectionsClickable())
		self.verticalHeader().setSectionsMovable(inputTableView.verticalHeader().sectionsMovable())
		
		# Copy scroll bars policy
		self.setVerticalScrollBarPolicy(inputTableView.verticalScrollBarPolicy())
		self.setHorizontalScrollBarPolicy(inputTableView.horizontalScrollBarPolicy())

	def dragEnterEvent(self, event):
		event.accept()

	def dragMoveEvent(self, event):
		event.accept()

	def dropEvent(self, event):
		source = event.source()
		if isinstance(source, QtWidgets.QTableView):
			targetModel = self.model()
			selectedIndexes = source.selectedIndexes()
			if selectedIndexes:
				targetModel.addItem(selectedIndexes)
				event.accept()
			else:
				event.ignore()
		else:
			super().dropEvent(event)