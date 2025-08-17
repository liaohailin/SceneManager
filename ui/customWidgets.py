from Qt.QtGui import (QPainter, QPolygon, QColor, QCursor)
from Qt.QtCore import (QPoint, QEvent, QObject, QRect)
from Qt.QtWidgets import (QComboBox, QWidget, QMenu, QAction, QTabWidget)

class CustomTabWidget(QTabWidget):
	def resizeEvent(self, event):
		super(CustomTabWidget, self).resizeEvent(event)
		# Calculate the height of the QTabBar to be 1/3 of the QTabWidget's height
		newTabBarWidth = self.width()
		# Set the QTabBar width
		self.tabBar().setFixedWidth(newTabBarWidth)

class ArrowWidget(QWidget):
	def __init__(self, parent=None, color=QColor(0, 0, 0)):
		super(ArrowWidget, self).__init__(parent)
		self.setFixedSize(15, 15)
		self.color = color

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.Antialiasing)

		# Draw down arrow
		points = QPolygon([
			QPoint(2, 5),
			QPoint(7, 10),
			QPoint(12, 5)
		])

		painter.setBrush(self.color)
		painter.setPen(self.color)
		painter.drawPolygon(points)

	def setColor(self, color):
		self.color = color
		self.update()


class CustomComboBox(QComboBox):
	def __init__(self, parent=None):
		super(CustomComboBox, self).__init__(parent)
		# Create custom arrow widget
		self.arrow_widget = ArrowWidget(self)

	def resizeEvent(self, event):
		super(CustomComboBox, self).resizeEvent(event)
		# Position the arrow widget
		self.arrow_widget.move(self.width() - 20, (self.height() - self.arrow_widget.height()) // 2)

	def setArrowColor(self, color):
		self.arrow_widget.setColor(color)


class ContextMenuHandler(QObject):
	def __init__(self, parent=None):
		super(ContextMenuHandler, self).__init__(parent)
		self.tableView = parent

	def eventFilter(self, source, event):
		if event.type() == QEvent.ContextMenu and source is self.tableView:
			index = self.tableView.indexAt(self.tableView.viewport().mapFromGlobal(QCursor.pos()))
			if index.isValid():
				context_menu = QMenu(self.tableView)
				# adding a remove submenu
				action = QAction("Remove", self.tableView)
				action.triggered.connect(lambda: self.removeItem(index))
				context_menu.addAction(action)
				# Adding a promote submenu
				if not self.tableView.model().inShotPkg(index):
					promotableACPs = self.tableView.model().getPromotableACPs(index)
					if promotableACPs:
						submenu = QMenu("Promote", self.tableView)
						for acp in promotableACPs:
							action = QAction(acp.name, self.tableView)
							action.triggered.connect(lambda acp=acp, index=index: self.promoteItem(acp, index))
							submenu.addAction(action)
						context_menu.addMenu(submenu)
				context_menu.exec_(event.globalPos())
				return True
		return False

	def promoteItem(self, targetACP, itemIndex):
		#promote selected index item to target name/prefix
		self.tableView.model().promoteItem(itemIndex, targetACP)
	
	def removeItem(self, index):
		self.tableView.model().removeItem(index)