#!/usr/bin/env python

from collections import OrderedDict, defaultdict
import json
import os
import platform
import subprocess
import webbrowser


class Workbench_Model:
    def __init__(self):
        self._workspaces = OrderedDict()
        self._open_doc = defaultdict(lambda: 'open ')
        self._open_doc['Windows'] = 'start '
        self._platform = platform.system()

    # ------------ WORKSPACES ------------

    def add_workspace(self, ws_name):
        self._workspaces[ws_name] = OrderedDict()

    def get_workspaces(self):
        return list(self._workspaces.keys())  # Python 3.0+ conversion

    def delete_workspace(self, ws_name):
        del self._workspaces[ws_name]

    # ------------ APPS ------------

    def get_app_names(self, ws_name):
        return self._workspaces[ws_name].keys()

    def get_app_icon(self, ws_name, app_name):
        return self._workspaces[ws_name][app_name][1]

    def add_app(self, ws_name, app_path, icon_path):
        app_name = os.path.splitext(os.path.basename(app_path))[0]
        self._workspaces[ws_name][app_name] = [app_path, icon_path]

    def delete_app(self, ws_name, app_name):
        del self._workspaces[ws_name][app_name]

    def reorder_apps(self, ws_name, app_list):
        if self._workspaces[ws_name].keys() != app_list:
            temp = OrderedDict()
            for name in app_list:
                temp[name] = self._workspaces[ws_name][name]
            self._workspaces[ws_name] = temp

    def run_app(self, ws_name, app_name):
        _file = self._workspaces[ws_name][app_name][0]
        if os.path.exists(_file):
            try:
                subprocess.Popen(_file)
            except:
                os.system(self._open_doc[self._platform] + _file)
        else:
            raise ValueError('Program no longer exists?')

    def external_link(self):
        webbrowser.open('https://www.github.com/eabdiel')

    # ------------ JSON ------------

    def write_json_file(self, path):
        with open(path, 'w') as js_file:
            json.dump(self._workspaces, js_file)

    def read_json_file(self, path):
        with open(path, 'r') as js_file:
            self._workspaces = OrderedDict(json.load(js_file))

# github.com/eabdiel
