from PyQt5 import QtWidgets, QtCore, QtGui
from libmproxy import flow
from copy import deepcopy
from libmproxy.protocol.http import HTTPResponse


class FlowDetails(QtWidgets.QWidget):
    saveClicked = QtCore.pyqtSignal(HTTPResponse)

    def __init__(self, conn, parent=None, editable=False):
        QtWidgets.QWidget.__init__(self, parent)
        self.conn = conn
        layout = QtWidgets.QVBoxLayout()
        self.flow_details_tabs = FlowDetailsTabs(conn, editable)
        layout.addWidget(self.flow_details_tabs)
        if editable:
            button = QtWidgets.QPushButton('Save')
            button.setFixedWidth(100)
            button.clicked.connect(self.on_save)
            layout.addWidget(button)
            layout.setAlignment(button, QtCore.Qt.AlignRight)

        self.setLayout(layout)
        self.show()

    def on_save(self):
        f = self.flow_details_tabs.get_edited_flow()
        if self.conn.headers.get_first('content-encoding'):
            f.encode(self.conn.headers.get_first('content-encoding'))
        self.saveClicked.emit(f)


class FlowDetailsTabs(QtWidgets.QTabWidget):
    def __init__(self, conn, editable=False):
        QtWidgets.QTabWidget.__init__(self)
        self.conn = deepcopy(conn)
        self.create_tabs(editable)

    def create_tabs(self, editable):
        self.header_details = Headers(self.conn, editable)
        self.content_details = ContentDetails(self.conn, editable)
        self.insertTab(0, self.header_details, "Headers")
        self.insertTab(1, self.content_details, "Content")

    def get_edited_flow(self):
        self.conn.headers = self.header_details.get_headers()
        if hasattr(self.conn, 'code'):
            self.conn.code = self.header_details.get_code()
        self.conn.content = self.content_details.get_content()
        return self.conn


class Headers(QtWidgets.QWidget):
    def __init__(self, conn, editable=False):
        QtWidgets.QWidget.__init__(self)
        layout = QtWidgets.QVBoxLayout()

        if hasattr(conn, 'url'):
            layout.addWidget(QtWidgets.QLabel(conn.url))

        self.headers = HeaderDetails(conn, editable)
        layout.addWidget(self.headers)

        if editable:
            add_header_btn = QtWidgets.QPushButton('Add header')
            add_header_btn.clicked.connect(self.headers.add_new_header)
            layout.addWidget(add_header_btn)

        if hasattr(conn, 'code'):
            self.code = QtWidgets.QLineEdit(str(conn.code))
            if not editable:
                self.code.setReadOnly(True)
            layout.addWidget(self.code)
        self.setLayout(layout)

    def get_headers(self):
        return self.headers.get_headers()

    def get_code(self):
        return int(str(self.code.text()))


class HeaderDetails(QtWidgets.QListWidget):
    def __init__(self, conn, editable=False):
        QtWidgets.QListWidget.__init__(self)
        if editable:
            self.itemDoubleClicked.connect(self.editItem)
            self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self.show_context_menu)
        for key, value in conn.headers:
            item = QtWidgets.QListWidgetItem(str(key)+': '+str(value))
            if editable:
                item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            self.addItem(item)

    def get_headers(self):
        headers = []
        for i in range(0, self.count()):
            item = self.item(i)
            split_index = str(item.text()).find(':')
            key = (str(item.text())[0:split_index]).strip()
            value = (str(item.text())[split_index+1::]).strip()
            headers.append([key, value])
        return flow.ODictCaseless(headers)

    def add_new_header(self):
        new_header = QtWidgets.QListWidgetItem('Key: value')
        new_header.setFlags(new_header.flags() | QtCore.Qt.ItemIsEditable)
        self.addItem(new_header)

    def show_context_menu(self, QPos):
        self.listMenu = QtWidgets.QMenu()
        remove_header = self.listMenu.addAction('Remove header')
        remove_header.triggered.connect(self.remove_header)
        parentPosition = self.mapToGlobal(QtCore.QPoint(0, 0))
        self.listMenu.move(parentPosition + QPos)
        self.listMenu.show()

    def remove_header(self):
        self.takeItem(self.currentRow())


class ContentDetails(QtWidgets.QTextEdit):
    def __init__(self, conn, editable=False):
        QtWidgets.QTextEdit.__init__(self)
        self.doc = QtGui.QTextDocument()
        if 'content-encoding' in conn.headers.keys():
            conn.decode()
        self.doc.setPlainText(conn.content)
        self.setDocument(self.doc)

    def get_content(self):
        return str(self.toPlainText())