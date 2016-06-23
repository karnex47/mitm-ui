from PyQt5 import QtCore, QtWidgets
from flowdetails import FlowDetails

class DetailsView(QtWidgets.QDialog):
    def __init__(self, f):
        QtWidgets.QDialog.__init__(self)
        layout = QtWidgets.QHBoxLayout()
        tabs = DetailsTabs(self)
        tabs.set_flow(f)
        layout.addWidget(tabs)
        self.setLayout(layout)
        self.setWindowTitle(f.request.url)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.exec_()


class DetailsTabs(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        QtWidgets.QTabWidget.__init__(self, parent)
        self.show()

    def set_flow(self, f):
        self.clear()
        if f.request:
            self.addTab(FlowDetails(f.request), "Request")
        if f.response:
            self.addTab(FlowDetails(f.response), "Response")