from libmproxy import flow
from PyQt5 import QtCore
from copy import deepcopy
import re
from config import resource_path
from libmproxy.protocol.http import HTTPResponse

class ControllerMaster(flow.FlowMaster):
    def __init__(self, server, state, options):
        flow.FlowMaster.__init__(self, server, state)
        if not options:
            options = []

    def handle_request(self, f):
        flow.FlowMaster.handle_request(self, f)

        if f.request.host == 'mitmcert.it':
            responseHeaders = flow.ODictCaseless([('content-type', 'application/x-x509-ca-cert')])
            cert_file = open(resource_path('mitmproxy/mitmproxy-ca-cert.pem'), 'rb')
            cert_content = cert_file.read()
            cert_file.close()
            responseHeaders['Content-Length'] = [len(cert_content)]
            responseHeaders['Content-Disposition'] = ['inline; filename=mitmproxy-ca-cert.pem']
            resp = HTTPResponse([1,1], 200, 'OK', responseHeaders, cert_content)
            f.reply(resp)
            return

        auto_response = self.state.get_auto_response_data(f.request.url)
        if auto_response and auto_response['active'] and auto_response['method'] == f.request.method:
            response = deepcopy(auto_response['response'])
            response_headers = []
            for key, value in response.headers:
                if key == "Content-Length":
                    response_headers.append(["Content-Length", len(response.content)])
                elif key == 'Cache-Control' or key == 'Pragma' or key == 'Expires':
                    continue
                else:
                    response_headers.append([key, value])

            response_headers.append(['Cache-Control', 'no-cache, no-store, must-revalidate'])
            response_headers.append(['Pragma', 'no-cache'])
            response_headers.append(['Expires', '0'])
            response.headers = flow.ODictCaseless(response_headers)
            f.reply(response)

        elif f:
            f.reply()

    def handle_response(self, f):
        flow.FlowMaster.handle_response(self, f)
        if f:
            f.reply()

    def get_headers(self, conn):
        hdr_items = tuple(tuple(i) for i in conn.headers.lst)
        return flow.ODictCaseless([list(i) for i in hdr_items])



class ControllerState(flow.State, QtCore.QObject):
    updateList = QtCore.pyqtSignal(int, str)
    searchChanged = QtCore.pyqtSignal()
    stateUpdated = QtCore.pyqtSignal()

    def __init__(self):
        flow.State.__init__(self)
        QtCore.QObject.__init__(self)
        self._replay = []
        self._auto_respond = {}
        self.search_string = ""

    def set_data_from_saved_state(self, saved_sate):
        self._auto_respond = saved_sate['auto_response']
        self._replay = saved_sate['replay']
        self.stateUpdated.emit()

    def add_request(self, f):
        ret = flow.State.add_request(self, f)
        self.update_view(self.view.index(f), 'add')
        return ret

    def add_response(self, f):
        ret = flow.State.add_response(self, f)
        self.update_view(self.view.index(f), 'update')
        return ret

    def add_error(self, f):
        ret = flow.State.add_error(self, f)
        self.update_view(self.view.index(f), 'update')
        return ret

    def recalculate_view(self):
        ret = flow.State.recalculate_view(self)
        self.update_view()
        return ret

    def delete_flow(self, f):
        index = self.view.index(f)
        ret = flow.State.delete_flow(self, f)
        self.update_view(index, 'delete')
        return ret

    def clear_view(self):
        self.view = []

    def update_view(self, index=None, mode=''):
        self.updateList.emit(index, mode)

    def get_auto_response_keys(self):
        return self._auto_respond.keys()

    def add_auto_response(self, key, value):
        self._auto_respond[key] = value

    def remove_auto_response(self, key):
        self._auto_respond.pop(key, None)

    def get_auto_response_data(self, key):
        try:
            return self._auto_respond[key]
        except KeyError:
            for url in self._auto_respond.keys():
                if self.get_match_type(url) == 'REGEX' and re.compile(url).match(key):
                    return self._auto_respond[url]
            return None

    def set_auto_response_active(self, key, active):
        self._auto_respond[key]['active'] = bool(active)

    def get_match_type(self, key):
        return self._auto_respond[key]['matchType']

    def set_match_type(self, key, value):
        self._auto_respond[key]['matchType'] = value

    def set_auto_response(self, key, response):
        self._auto_respond[key]['response'] = response

    def get_cached_response(self, key):
        return self._auto_respond[key]['response']

    def set_content_file_path(self, key, file_path):
        self._auto_respond[key]['file'] = file_path

    def get_content_file_path(self, key):
        return self._auto_respond[key]['file']

    def replace_auto_response_key(self, oldKey, newKey):
        value = deepcopy(self._auto_respond[oldKey])
        self.remove_auto_response(oldKey)
        self.add_auto_response(newKey, value)

    def set_search_string(self, string):
        string = str(string)
        string = string.strip()
        self.search_string = str(string)
        self.searchChanged.emit()