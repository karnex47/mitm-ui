from PyQt5 import QtCore, QtWidgets, QtGui
from detailsview import DetailsView
from libmproxy.protocol.http import HTTPFlow


class FlowListModel(QtCore.QAbstractListModel):
    def __init__(self, state, parent=None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.state = state
        self._data = self.state.view
        self.state.updateList.connect(self.update_list)
        self.state.searchChanged.connect(self.hightlight_matches)

    def rowCount(self, QModelIndex_parent=None, *args, **kwargs):
        return len(self._data)

    def data(self, QModelIndex, int_role=None):
        if int_role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self._data[QModelIndex.row()])
        return QtCore.QVariant()

    def update_list(self, index, mode):
        if not index:
            self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(0, len(self._data)), [])
        elif mode == 'add':
            self.rowsInserted.emit(self.createIndex(index, 0), index, index)
        elif mode == 'update':
            pass
        elif mode == 'delete':
            pass

    def hightlight_matches(self):
        for (i, f) in enumerate(self._data):
            if not f.request.url.find(self.state.search_string) == -1:
                index = self.createIndex(i, 0)
                self.dataChanged.emit(index, index)


    def getFlowData(self, index):
        return self._data[index.row()]

    def hasHighlight(self, index):
        return self.state.search_string != "" and self._data[index.row()].request.url.find(self.state.search_string) != -1


class FlowListItemDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None, *args):
        QtWidgets.QStyledItemDelegate.__init__(self, parent, *args)
        self.model = parent.model

    def paint(self, painter, option, index):
        options = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(options, index)
        painter.save()
        style = QtWidgets.QApplication.style() if options.widget is None else options.widget.style()
        doc = QtGui.QTextDocument()
        text = self.getHTMLFromFlow(self.model.getFlowData(index), self.model.hasHighlight(index))
        doc.setHtml(text)
        options.text = ""
        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, options, painter)
        ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()
        textRect = style.subElementRect(QtWidgets.QStyle.SE_ItemViewItemText, options)
        painter.save()
        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))
        doc.documentLayout().draw(painter, ctx)
        painter.restore()

    def sizeHint(self, option, index):
        options = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(options,index)
        doc = QtGui.QTextDocument()
        doc.setHtml(options.text)
        doc.setTextWidth(doc.textWidth())
        return QtCore.QSize(doc.textWidth(), doc.size().height())

    def getHTMLFromFlow(self, f, highlight=False):
        html = '<div style="{0}">' \
               '<span>{1}</span>' \
               '<span class="spacer">  </span>' \
               '<span"><strong>{2}</strong></span>' \
               '<span class="spacer">  </span>' \
               '<span>{3}</span>' \
               '</div>'
        style = 'color: black;'
        code = '   '
        if f.live:
            style = 'color: grey;'
        if f.error:
            style = 'color: red;'
        if f.response:
            code = f.response.code
            color = 'green' if 200 <= code <= 299 else 'purple' if 300 <= code <= 399 else 'red' if code >= 400 else 'black'
            code = '<span style="color: %s">%d</span>'%(color, code)
        if highlight:
            style += "background: yellow;"
        return html.format(style, code, f.request.method, f.request.url)


class FlowList(QtWidgets.QListView):
    addToAutoResponder = QtCore.pyqtSignal(HTTPFlow)
    addToReplay = QtCore.pyqtSignal(HTTPFlow)
    itemClicked = QtCore.pyqtSignal(HTTPFlow)

    def __init__(self, state):
        super(FlowList, self).__init__()
        self.model = FlowListModel(state)
        self.setModel(self.model)
        self.setItemDelegate(FlowListItemDelegate(self))
        self.setStyleSheet(':item:selected:active {background: lightblue}')

        self.clicked.connect(self.on_flow_list_click)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.show()

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def on_flow_list_click(self, index):
        f = self.model.getFlowData(index)
        self.itemClicked.emit(f)

    def show_flow_details(self):
        f = self.model.getFlowData(self.currentIndex())
        DetailsView(f)

    def show_context_menu(self, QPos):
        self.listMenu = QtWidgets.QMenu()
        view_details = self.listMenu.addAction("View Details")
        add_to_autoresponder = self.listMenu.addAction("Add to auto-responder")
        add_to_replay = self.listMenu.addAction("Add to replay")
        view_details.triggered.connect(self.show_flow_details)
        add_to_replay.triggered.connect(self.add_to_replay_clicked)
        add_to_autoresponder.triggered.connect(self.add_to_autoresponder_clicked)
        parentPosition = self.mapToGlobal(QtCore.QPoint(0, 0))
        self.listMenu.move(parentPosition + QPos)
        self.listMenu.show()

    def add_to_replay_clicked(self):
        f = self.model.getFlowData(self.currentIndex())
        self.addToReplay.emit(f)

    def add_to_autoresponder_clicked(self):
        f = self.model.getFlowData(self.currentIndex())
        self.addToAutoResponder.emit(f)
