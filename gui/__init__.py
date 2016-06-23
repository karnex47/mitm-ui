from PyQt5.QtWidgets import QMainWindow
from PyQt5 import QtWidgets, QtGui
from mainwidget import MainGui
from libmproxy.proxy.server import ProxyServer
from config import AppConfig, resource_path
from settingsview import SettingsDialog
from importexportview import ImportExportDialog

appStyle = """
QToolBar {{background: black}}
QIcon {{height: 10px; width: 10px}}
"""

class MainWindow(QMainWindow):
    def __init__(self, options):
        QMainWindow.__init__(self)

        self.ui = MainGui(self.get_server(), options)
        self.setCentralWidget(self.ui)

        self.statusBar()
        if self.ui.isServerRunning():
            self.statusBar().showMessage('Server started on port '+ str(AppConfig.Instance().getProxyConfig().port))
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(QtWidgets.QAction("Settings", self))

        toolbar = self.addToolBar('toolbar')
        self.server_control_action = QtWidgets.QAction(self.get_server_status_icon(), "Start/Stop Capture", self)
        self.server_control_action.triggered.connect(self.toggle_server)
        clear_action = QtWidgets.QAction(QtGui.QIcon(resource_path('assets/clear-icon.png')), "Clear", self)
        clear_action.triggered.connect(self.ui.clear_view)
        settings_action = QtWidgets.QAction(QtGui.QIcon(resource_path('assets/gear-icon.png')), "Settings", self)
        settings_action.triggered.connect(self.show_settings)
        search_field = QtWidgets.QLineEdit();
        search_field.textChanged.connect(self.ui.search_changed)
        add_cert = QtWidgets.QAction(QtGui.QIcon(resource_path('assets/cert-icon.png')), "Install certificate (opens 'mitmcert.it')", self)
        add_cert.triggered.connect(self.open_browser_to_cert)
        import_export_action = QtWidgets.QAction(QtGui.QIcon(resource_path('assets/import-export-icon.png')), "Import/export state from/to file", self)
        import_export_action.triggered.connect(self.show_import_export)
        toolbar.addAction(clear_action)
        toolbar.addAction(self.server_control_action)
        toolbar.addAction(settings_action)
        toolbar.addSeparator()
        toolbar.addWidget(QtWidgets.QLabel("Filter:"))
        toolbar.addWidget(search_field)
        toolbar.addSeparator()
        toolbar.addAction(import_export_action)
        toolbar.addAction(add_cert)
        toolbar.setMovable(False)
        self.setStyleSheet(appStyle)

        self.show()

    def toggle_server(self):
        if self.ui.isServerRunning():
            self.stopServer()
        else:
            self.startServer()

    def startServer(self):
        self.ui.start_server(self.get_server())
        if self.ui.isServerRunning():
            self.statusBar().showMessage('Server started on port '+ str(AppConfig.Instance().getProxyConfig().port))
        self.server_control_action.setIcon(self.get_server_status_icon())

    def stopServer(self):
        self.statusBar().showMessage('Server stopped')
        self.ui.shut_down()
        self.server_control_action.setIcon(self.get_server_status_icon())

    def get_server(self):
        try:
            return ProxyServer(AppConfig.Instance().getProxyConfig())
        except Exception, e:
            self.statusBar().showMessage("Error: "+e.message)

    def get_server_status_icon(self):
        if self.ui.isServerRunning():
            return QtGui.QIcon(resource_path('assets/off-icon.png'))
        return QtGui.QIcon(resource_path('assets/on-icon.png'))

    def get_server_status_text(self):
        if self.ui.isServerRunning():
            return "Stop Capture"
        return "Start Capture"

    def show_settings(self):
        settings_dialog = SettingsDialog()
        settings_dialog.settingsChanged.connect(self.onSettingsClose)

    def onSettingsClose(self, isSettingsChanged):
        print isSettingsChanged

    def show_import_export(self):
        ImportExportDialog(self.ui.load_state, self.ui.save_state)

    def open_browser_to_cert(self):
        import webbrowser
        webbrowser.open('http://mitmcert.it')

    def closeEvent(self, event):
        self.ui.terminate()