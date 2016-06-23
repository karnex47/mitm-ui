from PyQt5 import QtCore, QtWidgets

class ImportExportDialog(QtWidgets.QDialog):
    def __init__(self, onImport, onExport):
        QtWidgets.QDialog.__init__(self)
        self.onImport = onImport
        self.onExport = onExport
        layout = QtWidgets.QGridLayout()
        layout.addWidget(QtWidgets.QLabel("Path:"), 0, 0)
        self.file_input = QtWidgets.QLineEdit()
        layout.addWidget(self.file_input, 0, 1)
        file_dialog_btn = QtWidgets.QPushButton("...")
        file_dialog_btn.clicked.connect(self.show_file_dialog)
        layout.addWidget(file_dialog_btn, 0, 2)
        self.setWindowTitle("Import/Export State")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        import_btn = QtWidgets.QPushButton("Import")
        import_btn.clicked.connect(self.triggerImport)
        import_btn.setFixedWidth(100)
        layout.addWidget(import_btn, 1,1)
        layout.setAlignment(import_btn, QtCore.Qt.AlignRight)
        export_btn = QtWidgets.QPushButton("Export")
        export_btn.clicked.connect(self.triggerExport)
        export_btn.setFixedWidth(100)
        layout.addWidget(export_btn, 1,2)
        layout.setAlignment(export_btn, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.exec_()

    def show_file_dialog(self):
        fileDialog = QtWidgets.QFileDialog()
        fileDialog.fileSelected.connect(self.set_file_path)
        fileDialog.exec_()

    def set_file_path(self, path):
        self.file_input.setText(path)

    def triggerImport(self):
        path = str(self.file_input.text())
        self.onImport(path)

    def triggerExport(self):
        path = str(self.file_input.text())
        self.onExport(path)
