from PyQt5 import QtCore, QtWidgets
from config import AppConfig
from libmproxy import platform

class SettingsDialog(QtWidgets.QDialog):
    settingsChanged = QtCore.pyqtSignal(bool)
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        layout = QtWidgets.QVBoxLayout()
        settingView = SettingsView()
        settingView.settingsChanged.connect(self.settingChanged)
        settingView.settingsError.connect(self.settingsError)
        layout.addWidget(settingView)
        self.statusBar = QtWidgets.QLabel("")
        layout.addWidget(self.statusBar)
        self.setLayout(layout)
        self.setWindowTitle("Settings")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.exec_()

    def settingChanged(self, isChnaged):
        self.statusBar.setStyleSheet("QLabel {color: blue}")
        if isChnaged:
            self.statusBar.setText("Settings changed. please restart server for changes to take effect")
        else:
            self.statusBar.setText("Settings not modified")

    def settingsError(self, message):
        self.statusBar.setStyleSheet("QLabel {color: red}")
        self.statusBar.setText("Error: "+message)



class SettingsView(QtWidgets.QWidget):
    settingsChanged = QtCore.pyqtSignal(bool)
    settingsError = QtCore.pyqtSignal(str)
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        layout = QtWidgets.QGridLayout()
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(TextEditWithLabel("Host:", "host", "Address to bind proxy to (defaults to all interfaces)"))
        left_layout.addWidget(TextEditWithLabel("Port:", "port", "Proxy service port"))
        left_layout.addWidget(TextEditWithLabel("Ignore hosts:", "ignore_hosts", "Ignore host and forward all traffic without processing it. \n"
                                                                            "In transparent mode, it is recommended to use an IP address (range), \n"
                                                                            "not the hostname. In regular mode, only SSL traffic is ignored and the \n"
                                                                            "hostname should be used. The supplied value is interpreted as a regular \n"
                                                                            "expression and matched on the ip or the hostname"))
        left_layout.addWidget(TextEditWithLabel("TCP hosts:", "tcp_hosts", "Generic TCP SSL proxy mode for all hosts that match the pattern \n"))
        left_layout.addWidget(TextEditWithLabel("SSL ports:", "ssl_ports", "Specify destination ports which are assumed to be SSL"))
        layout.addLayout(left_layout, 0, 0)
        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(ProxyModeSelector())
        right_layout.addWidget(AuthenticationSettings())
        layout.addLayout(right_layout, 0, 1)
        save_btn = QtWidgets.QPushButton("Save")
        save_btn.clicked.connect(self.saveConfigs)
        save_btn.setFixedWidth(100)
        layout.addWidget(save_btn, 1,1)
        layout.setAlignment(save_btn, QtCore.Qt.AlignRight)
        layout.setSpacing(1)
        self.setLayout(layout)

    def saveConfigs(self):
        newConfigs = {}
        for i in range(self.layout().count()):
            layout = self.layout().itemAt(i)
            if not layout.widget():
                for j in range(layout.count()):
                    item = layout.itemAt(j).widget()
                    if hasattr(item, "getData"):
                        data = item.getData()
                        if data:
                            if type(data) is dict:
                                newConfigs.update(data)
                            else:
                                newConfigs[data[0]] = data[1]
        if not len(newConfigs) == 0:
            try:
                AppConfig.Instance().updateConfig(newConfigs)
                self.settingsChanged.emit(True)
            except ValueError, e:
                self.settingsError.emit(e.message)
        else:
            self.settingsChanged.emit(False)


class TextEditWithLabel(QtWidgets.QWidget):
    def __init__(self, label, key, description=""):
        self.key = key
        self.data = AppConfig.Instance().getConfig()[key]
        self.display = self.getDisplay(self.data)
        QtWidgets.QWidget.__init__(self)
        layout = QtWidgets.QGridLayout()
        layout.addWidget(QtWidgets.QLabel(label), 0, 0)
        self.input = QtWidgets.QLineEdit(self.display)
        layout.addWidget(self.input, 0, 1)
        description = QtWidgets.QLabel(str(description))
        description.setStyleSheet("QLabel {color: grey}")
        layout.addWidget(description, 1, 0, 1, 2)
        layout.setVerticalSpacing(1)
        self.setLayout(layout)

    def getData(self):
        if str(self.input.text()) == self.display:
            return None
        else:
            self.display = str(self.input.text())
            return self.key, self.getDataFromDisplay(self.display)

    def getDataFromDisplay(self, display):
        if self.data:
            if type(self.data) is int:
                return int(display)
            if type(self.data) is list:
                return [i.strip() for i in display.split(',')]
        return display

    def getDisplay(self, data):
        if data:
            if type(data) is int:
                return str(data)
            if type(data) is list:
                return ', '.join(str(item) for item in data)
            return data
        return ""

    def setInputDisabled(self, state):
        self.input.setDisabled(state)

class ProxyModeSelector(QtWidgets.QWidget):
    proxyModes = {
                     "regular_proxy": "Set regular proxy mode",
                     "reverse_proxy": "Forward all requests to upstream HTTP server: http[s][2http[s]]://host[:port]",
                     "socks_proxy": "Set SOCKS5 proxy mode.",
                     "transparent_proxy": "Set transparent proxy mode.",
                     "upstream_proxy": "Forward all requests to upstream proxy server: http://host[:port]"}
    current_index = 0
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        if not platform.resolver:
            self.proxyModes.pop("transparent_proxy", None)
        mode = "regular_proxy"
        config = AppConfig.Instance().getConfig()
        for index, proxyMode in enumerate(self.proxyModes.keys()):
            if config[proxyMode]:
                mode = proxyMode
                self.current_index = index
                break

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Select proxy mode:'))

        self.radio_group = QtWidgets.QButtonGroup()
        radio_group_layout = QtWidgets.QVBoxLayout()
        for index, proxyMode in enumerate(self.proxyModes.keys()):
            btn = QtWidgets.QRadioButton(proxyMode.replace('_', ' ').title())
            btn.setChecked(mode == proxyMode)
            self.radio_group.addButton(btn)
            self.radio_group.setId(btn, index)
            item_layout = QtWidgets.QHBoxLayout()
            item_layout.addWidget(btn)
            description = QtWidgets.QLabel(self.proxyModes[proxyMode])
            description.setStyleSheet("QLabel {color: grey}")
            description.setAlignment(QtCore.Qt.AlignLeft)
            item_layout.addWidget(description)
            radio_group_layout.addLayout(item_layout)
        self.radio_group.buttonClicked.connect(self.set_proxy_mode)
        layout.addLayout(radio_group_layout)

        url_input_layout = QtWidgets.QGridLayout()
        url_input_layout.addWidget(QtWidgets.QLabel("Upstream server:"), 0, 0)
        self.input = QtWidgets.QLineEdit(config['upstream_server'] or "")
        if not mode in ["reverse_proxy", "upstream_proxy"]:
            self.input.setDisabled(True)
        url_input_layout.addWidget(self.input, 0, 1)
        description = QtWidgets.QLabel(str("Upstream server for Reverse/Upstream Proxy (required)"))
        description.setStyleSheet("QLabel {color: grey}")
        url_input_layout.addWidget(description, 1, 0, 1, 2)
        layout.addLayout(url_input_layout)
        self.setLayout(layout)

        
    def set_proxy_mode(self, button):
        self.current_index = self.radio_group.id(button)
        if self.proxyModes.keys()[self.current_index] in ["reverse_proxy", "upstream_proxy"]:
            self.input.setDisabled(False)
        else:
            self.input.setDisabled(True)

    def getDisplayData(self):
        mode = self.proxyModes.keys()[self.current_index]
        if mode in ["reverse_proxy", "upstream_proxy"]:
            return mode, str(self.input.text())
        else:
            return mode, True

    def getData(self):
        data = self.getDisplayData()
        config = AppConfig.Instance().getConfig()
        if config[data[0]] == data[1]:
            return None
        if data[0] in ["reverse_proxy", "upstream_proxy"]:
            return {
                data[0]: True,
                "upstream_server": data[1]
            }
        return data


class AuthenticationSettings(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        layout = QtWidgets.QVBoxLayout()
        self.singleUserConfig = SingleUserConfig()
        layout.addWidget(self.singleUserConfig)
        self.non_anon_checkbox = QtWidgets.QCheckBox("Allow access to any user long as a credentials are specified.")
        self.non_anon_checkbox.setCheckState(2 if AppConfig.Instance().getConfig()['auth_nonanonymous'] else 0)
        layout.addWidget(self.non_anon_checkbox)
        self.apacheConfig = ApacheConfig()
        layout.addWidget(self.apacheConfig)
        self.setLayout(layout)

    def getData(self):
        data = {}
        data.update(self.singleUserConfig.getData())
        if not self.non_anon_checkbox.checkState() == 2 if AppConfig.Instance().getConfig()['auth_nonanonymous'] else 0:
            data['auth_nonanonymous'] = self.non_anon_checkbox.checkState() == 2
        data.update(self.apacheConfig.getData())
        return data


class SingleUserConfig(QtWidgets.QWidget):
    enabled = False

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        config = AppConfig.Instance().getConfig()
        self.enabled = config['requires_singleuser']
        credentials = config["auth_singleuser"]
        user_name = ""
        password = ""
        if credentials and len(credentials.split(':')) == 2:
            user_name = credentials.split(':')[0]
            password = credentials.split(':')[1]
        layout = QtWidgets.QGridLayout()
        enable_checkbox = QtWidgets.QCheckBox("Allows access to a single user")
        enable_checkbox.stateChanged.connect(self.setAuthenticationEnabled)
        layout.addWidget(enable_checkbox, 0, 0, 1, 2)
        layout.addWidget(QtWidgets.QLabel("Username"), 1, 0)
        self.user_name = QtWidgets.QLineEdit(user_name)
        self.user_name.setEnabled(self.enabled)
        layout.addWidget(self.user_name, 1, 1)
        layout.addWidget(QtWidgets.QLabel("Password"), 2, 0)
        self.password = QtWidgets.QLineEdit(password)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password.setEnabled(self.enabled)
        layout.addWidget(self.password, 2, 1)
        enable_checkbox.setCheckState(2 if self.enabled else 0)
        layout.setContentsMargins(0, 11, 0, 11)
        self.setLayout(layout)

    def setAuthenticationEnabled(self, checked):
        self.enabled = checked == 2
        self.user_name.setEnabled(self.enabled)
        self.password.setEnabled(self.enabled)

    def getData(self):
        if self.enabled == AppConfig.Instance().getConfig()['requires_singleuser']:
            return {}
        return {
            "requires_singleuser": self.enabled,
            "auth_singleuser": str(self.user_name.text()) + ':' + str(self.password.text())
        }

class ApacheConfig(QtWidgets.QWidget):
    enabled = False
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        config = AppConfig.Instance().getConfig()
        self.enabled = config['requires_htpasswd']
        self.file_path = config['auth_htpasswd']
        layout = QtWidgets.QGridLayout()
        enable_checkbox = QtWidgets.QCheckBox("Allow access to users specified in an Apache htpasswd file.")
        enable_checkbox.stateChanged.connect(self.setAuthenticationEnabled)
        enable_checkbox.setCheckState(2 if self.enabled else 0)
        layout.addWidget(enable_checkbox, 0, 0, 1, 3)
        layout.addWidget(QtWidgets.QLabel("Path:"), 1, 0)
        self.file_input = QtWidgets.QLineEdit(self.file_path)
        layout.addWidget(self.file_input, 1, 1)
        file_dialog_btn = QtWidgets.QPushButton("...")
        file_dialog_btn.clicked.connect(self.show_file_dialog)
        layout.addWidget(file_dialog_btn, 1, 2)
        layout.setContentsMargins(0, 11, 0, 11)
        self.setLayout(layout)

    def setAuthenticationEnabled(self, checked):
        self.enabled = checked == 2

    def show_file_dialog(self):
        fileDialog = QtWidgets.QFileDialog()
        fileDialog.fileSelected.connect(self.set_file_path)
        fileDialog.exec_()

    def set_file_path(self, path):
        self.file_input.setText(path)

    def getData(self):
        data = {}
        if not self.enabled == AppConfig.Instance().getConfig()['requires_htpasswd']:
            data['requires_htpasswd'] = self.enabled
        if not str(self.file_input.text()) == AppConfig.Instance().getConfig()['auth_htpasswd']:
            data['auth_htpasswd'] = str(self.file_input.text())
        return data