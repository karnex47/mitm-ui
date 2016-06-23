from PyQt5 import QtCore, QtWidgets, QtGui
from flowdetails import FlowDetails
import copy, re, os, urllib2

class AutoResponder(QtWidgets.QWidget):
    def __init__(self, state):
        QtWidgets.QWidget.__init__(self)
        self.state = state
        self.create_window()
        self.show()

    def create_window(self):
        layout = QtWidgets.QVBoxLayout()
        layout.addStretch(1)

        self.model = CustomStandardListModel()
        for key in self.state.get_auto_response_keys():
            list_item = QtGui.QStandardItem(key)
            list_item.setCheckable(True)
            list_item.setFlags(list_item.flags() | QtCore.Qt.ItemIsEditable)
            if self.state.get_auto_response_data(key)['active']:
                list_item.setCheckState(2)
            else:
                list_item.setCheckState(0)
            self.model.appendRow(list_item)
        self.model.onItemChange.connect(self.on_list_item_change)
        self.response_list = QtWidgets.QListView()
        self.response_list.setModel(self.model)
        self.response_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.response_list.clicked.connect(self.set_stored_file_path)
        self.response_list.customContextMenuRequested.connect(self.show_context_menu)

        self.file_selector = FileSelector()
        self.file_selector.contentSet.connect(self.set_content_from_file)

        layout.addWidget(self.response_list)
        layout.addWidget(self.file_selector)

        layout.setStretchFactor(self.response_list, 99)
        layout.setStretchFactor(self.file_selector, 1)
        self.setLayout(layout)

    def add_auto_response_flow(self, f):
        url = f.request.url
        list_item = QtGui.QStandardItem(url)
        list_item.setCheckable(True)
        list_item.setCheckState(2)
        list_item.setFlags(list_item.flags() | QtCore.Qt.ItemIsEditable)
        self.model.appendRow(list_item)
        response = copy.deepcopy(f.response)
        response.decode()
        data = {
            "method": f.request.method,
            "active": True,
            "response": response,
            "match": url,
            "matchType": "EXACT",
            "file": ''
        }

        self.state.add_auto_response(url, data)

    def on_list_item_change(self, oldItem, newItem):
        if not oldItem.text() == newItem.text():
            self.state.replace_auto_response_key(str(oldItem.text()), str(newItem.text()))
        if not oldItem.checkState() == newItem.checkState():
            self.state.set_auto_response_active(str(newItem.text()), newItem.checkState())

        
    def show_context_menu(self, QPos):
        self.listMenu = QtWidgets.QMenu()
        edit_response = self.listMenu.addAction("Edit Response")
        edit_response.triggered.connect(self.edit_response_clicked)
        remove_response = self.listMenu.addAction("Remove Response")
        remove_response.triggered.connect(self.remove_response_clicked)
        escape = self.listMenu.addAction("Escape URL")
        escape.triggered.connect(self.escape_url)
        unescape = self.listMenu.addAction("Unescape URL")
        unescape.triggered.connect(self.unescape_url)

        key = str(self.model.itemFromIndex(self.response_list.currentIndex()).text())
        current_match_type = self.state.get_match_type(key)
        set_match_type_ag = QtWidgets.QActionGroup(self)
        set_match_type_ag.setExclusive(True)
        exact_match = QtWidgets.QAction("Match: EXACT", self)
        exact_match.setCheckable(True)
        exact_match.setChecked(current_match_type == "EXACT")
        re_match = QtWidgets.QAction("Match: REGEX", self)
        re_match.setCheckable(True)
        re_match.setChecked(current_match_type == "REGEX")
        a = set_match_type_ag.addAction(exact_match)
        self.listMenu.addAction(a)
        a = set_match_type_ag.addAction(re_match)
        self.listMenu.addAction(a)
        set_match_type_ag.triggered.connect(self.set_match_type)

        parentPosition = self.mapToGlobal(QtCore.QPoint(0, 0))
        self.listMenu.move(parentPosition + QPos)
        self.listMenu.show()

    def edit_response_clicked(self):
        key = str(self.model.itemFromIndex(self.response_list.currentIndex()).text())
        EditResponseDialog(key, self.state.get_cached_response(key), self.on_response_change)

    def on_response_change(self, key, response):
        self.state.set_auto_response(key, response)

    def remove_response_clicked(self):
        index = self.response_list.currentIndex()
        key = str(self.model.itemFromIndex(index).text())
        self.model.removeRow(index.row())
        self.state.remove_auto_response(key)

    def set_match_type(self, action):
        item = self.model.itemFromIndex(self.response_list.currentIndex())
        key = str(item.text())
        value = str(action.text()).split(':')[1].strip()
        self.state.set_match_type(key, value)
        if value == 'REGEX':
            self.escape_url(item)
        else:
            self.unescape_url(item)

    def escape_url(self, item=None):
        if not item:
            item = self.model.itemFromIndex(self.response_list.currentIndex())
        old_key = str(item.text())
        new_key = re.escape(old_key)
        item.setText(new_key)
        self.state.replace_auto_response_key(old_key, new_key)

    def unescape_url(self, item=None):
        if not item:
            item = self.model.itemFromIndex(self.response_list.currentIndex())
        old_key = str(item.text())
        new_key = re.sub(r'\\(.)', r'\1', old_key)
        item.setText(new_key)
        self.state.replace_auto_response_key(old_key, new_key)

    def set_stored_file_path(self, index):
        key = str(self.model.itemFromIndex(index).text())
        self.file_selector.set_file_path(self.state.get_content_file_path(key))

    def set_content_from_file(self, file_path):
        try:
            if file_path.strip() == '':
                content = None
            elif os.path.isfile(file_path):
                content_file = open(file_path, 'r')
                content = str(content_file.read())
                content_file.close()
            else:
                content_file = urllib2.urlopen(file_path)
                content = str(content_file.read())
                content_file.close()
            key = str(self.model.itemFromIndex(self.response_list.currentIndex()).text())
            self.state.set_content_file_path(key, file_path)
            if content:
                response = self.state.get_cached_response(key)
                response.content = content
                if response.headers.get_first('content-encoding'):
                    response.encode(self.conn.headers.get_first('content-encoding'))
                self.state.set_auto_response(key, response)
        except IOError, HTTPError:
            show_dialog("Cannot read file")


class CustomStandardListModel(QtGui.QStandardItemModel):
    onItemChange = QtCore.pyqtSignal(QtGui.QStandardItem, QtGui.QStandardItem)

    def setData(self, index, value, role):
        if role == QtCore.Qt.EditRole or role == QtCore.Qt.DisplayRole or role == QtCore.Qt.CheckStateRole:
            old = self.itemFromIndex(index).clone()
            ret = QtGui.QStandardItemModel.setData(self, index, value, role)
            new = self.itemFromIndex(index)
            self.onItemChange.emit(old, new)
            return ret



class FileSelector(QtWidgets.QWidget):
    contentSet = QtCore.pyqtSignal(str)

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.create()

    def create(self):
        layout = QtWidgets.QHBoxLayout()

        label = QtWidgets.QLabel("Respond with:")
        self.file_name = QtWidgets.QLineEdit()
        file_dialog_button = QtWidgets.QPushButton('...')
        file_dialog_button.clicked.connect(self.show_file_dialog)
        save_button = QtWidgets.QPushButton('Save')
        save_button.clicked.connect(self.send_file_content)

        layout.addWidget(label)
        layout.addWidget(self.file_name)
        layout.addWidget(file_dialog_button)
        layout.addWidget(save_button)

        self.setLayout(layout)
        self.show()

    def show_file_dialog(self):
        fileDialog = QtWidgets.QFileDialog()
        fileDialog.fileSelected.connect(self.set_file_path)
        fileDialog.exec_()
        
    def send_file_content(self):
        self.contentSet.emit(str(self.file_name.text()).strip())

    def set_file_path(self, path):
        self.file_name.setText(path)



class EditResponseDialog(QtWidgets.QDialog):
    def __init__(self, key, conn, callback):
        QtWidgets.QDialog.__init__(self)
        self.key = key
        self.callback = callback
        editor = FlowDetails(conn, self, True)
        editor.saveClicked.connect(self.on_save)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(editor)
        self.setLayout(layout)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.exec_()

    def on_save(self, response):
        print response
        self.callback(self.key, response)


def show_dialog(msg):
    dialog = QtWidgets.QDialog(str(msg))
    dialog.exec_()