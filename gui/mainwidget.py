from PyQt5 import QtWidgets, QtCore
from flowlistview import FlowList
from actionsview import ActionsView
from libmproxy.proxy.primitives import ProxyServerError
from controller import ControllerMaster, ControllerState
from cPickle import dump, load, PicklingError, UnpicklingError, HIGHEST_PROTOCOL
from threading import Thread
from config import resource_path


class ControllerThread(Thread):
    def __init__(self, server, state, options):
        Thread.__init__(self)
        self.controller = ControllerMaster(server, state, options)
        self.flow_list = QtCore.pyqtSignal(object)

    def run(self):
        try:
            self.controller.run()
        except ProxyServerError:
            print 'Could not run server'
        except AttributeError:
            print 'Could not run server'

    def terminate(self):
        try:
            self.controller.shutdown()
        except Exception, e:
            print e.message


class MainGui(QtWidgets.QWidget):
    def __init__(self, server, options, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        prev_instatnce_state = self.load_state()
        self.state = ControllerState()
        if prev_instatnce_state:
            self.state.set_data_from_saved_state(prev_instatnce_state)
        self.flow_list = FlowList(self.state)
        self.actions_view = ActionsView(self.state)
        self.show_main_widget(server, options)

    def show_main_widget(self, server, options):
        layout = QtWidgets.QHBoxLayout()
        splitter = QtWidgets.QSplitter()
        splitter.addWidget(self.flow_list)
        splitter.addWidget(self.actions_view)
        layout.addWidget(splitter)
        self.setLayout(layout)
        self.flow_list.setStyleSheet( """QListView:item:selected:active {background-color:red;}""")

        self.controllerThread = ControllerThread(server, self.state, options)
        self.flow_list.itemClicked.connect(self.set_flow_details)
        self.flow_list.addToAutoResponder.connect(self.add_auto_response)
        if server:
            self.controllerThread.start()

    def set_flow_details(self, f):
        self.actions_view.set_flow_details(f)

    def add_auto_response(self, f):
        self.actions_view.add_auto_response_flow(f)

    def search_changed(self, newSearch):
        self.state.set_search_string(newSearch)

    def clear_view(self):
        self.state.clear()

    def shut_down(self):
        if self.controllerThread.isAlive():
            self.controllerThread.terminate()
            self.controllerThread.join()

    def start_server(self, server=None, options=None):
        if self.controllerThread.isAlive():
            self.controllerThread.terminate()
            self.controllerThread.join()
        if server:
            self.controllerThread = ControllerThread(server, self.state, options)
        self.controllerThread.start()

    def isServerRunning(self):
        return self.controllerThread.isAlive()

    def load_state(self, path=None):
        if not path:
            path = resource_path('data')
        try:
            f = open(path, 'rb')
            data = load(f)
            f.close()
            return data
        except UnpicklingError:
            print 'Error loading data file, falling back to empty state'
            return None
        except IOError:
            print 'Error could not find file, falling back to empty state'
            return None

    def terminate(self):
        self.save_state()
        self.controllerThread.terminate()
        self.controllerThread.join()

    def save_state(self, path=None):
        print path
        if not path:
            path = resource_path('data')
        state_data = {}
        state_data['auto_response'] = self.state._auto_respond
        state_data['replay'] = self.state._replay
        try:
            f = open(path, 'wb')
            dump(state_data, f, HIGHEST_PROTOCOL)
            f.close()
        except PicklingError:
            print 'Error writing data file'