from Qt import QtCore, QtWidgets, QtGui


def addPaddingToRect(rect, padding):
	 return QtCore.QRect(
        rect.left() + padding,
        rect.top() + padding,
        rect.width() - 2 * padding,
        rect.height() - 2 * padding
    )


def getColoredPixmap(iconPath, color, width=100, height=100):
	""" Overridden from the class to allow us
		to give custom style to the child columns
		when they are expanded.
		Args:
			iconPath (str): path of icon
			color (QtColor): color of icon
			width (int): destination width of pixmap
			height (int): destination height of pixmap
		return: pixmap of colored icon
	"""
	pixmap = QtGui.QPixmap(iconPath)
	colored_pixmap = QtGui.QPixmap(pixmap.size())
	colored_pixmap.fill(QtCore.Qt.transparent)

	colored_painter = QtGui.QPainter(colored_pixmap)
	colored_painter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
	colored_painter.drawPixmap(0, 0, pixmap)
	colored_painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
	colored_painter.fillRect(colored_pixmap.rect(), color)
	colored_painter.end()
	# scale to designated size first
	colored_pixmap = colored_pixmap.scaled(width, height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
	return colored_pixmap