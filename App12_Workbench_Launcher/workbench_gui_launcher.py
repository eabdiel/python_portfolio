'''
QT designed gui for a workbench that
allows the user to quickly create, select and
delete workspaces that contain links to apps/files
for instant access.  App remains visible on the system tray.
'''

# !/usr/bin/env python
__version__ = '0.1'

from collections import defaultdict
import os
import sys

import Qt
from Qt import QtWidgets, QtCore, QtGui
import workbench_model

QT_VER = Qt.__binding__
PY_VER = sys.version[:3]

class Delete_Btn(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super(Delete_Btn, self).__init__(parent)
        self._my_parent = parent
        self._type = 'application/x-qabstractitemmodeldatalist'

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat(self._type):
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        if e.mimeData().hasFormat(self._type):
            self._my_parent.delete_item()
            e.accept()
        else:
            e.ignore()


class Workbench_Launcher_GUI(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Workbench_Launcher_GUI, self).__init__(parent)

        self._icons = QtWidgets.QFileIconProvider()
        self._my_path = os.path.dirname(os.path.realpath(__file__))
        images_path = os.path.join(self._my_path, 'images')
        full_path = os.path.join(images_path, 'Launcher.png')
        self._tpl_icon = QtGui.QIcon(full_path)

        self._workbench_launcher = workbench_model.Workbench_Model()

        self._edit_op = {
            True: self._edit_on,
            False: self._edit_off
        }
        self._app_instruction = True
        self._file_dialogs = defaultdict(lambda: self._file_dialog)
        self._file_dialogs['PyQt4'] = self._file_dialog_pyqt4
        self._dragging = None
        self._delete_op = {
            'workspace': self._delete_workspace,
            'application': self._delete_app
        }

        txt = f'Workbench Launcher {QT_VER}'
        self._settings = QtCore.QSettings(txt, 'Workbench_Launcher')
        name = f'{PY_VER}_{QT_VER}_data.json'
        path = os.path.join(self._my_path, 'data')
        self._json_file = os.path.join(path, name)

        d = defaultdict(lambda: self._get_settings)
        self._settings_op = defaultdict(lambda: d)

        self._setup()
        self._load_settings()
        self._edit_toggle()

    # ------------ SETUP UI ------------

    def _setup(self):
        v_layout = QtWidgets.QVBoxLayout(self)

        v_layout.addLayout(self._setup_header())
        v_layout.addLayout(self._setup_edit_options())
        v_layout.addWidget(self._setup_apps())

        self._setup_tray_icon()
        self._setup_connections()

        self.setWindowTitle(f'Workbench Launcher {__version__}')
        self.setWindowIcon(self._tpl_icon)
        flag = QtCore.Qt.WindowCloseButtonHint
        self.setWindowFlags(QtCore.Qt.Window | flag)
        self.resize(280, 175)

    def _setup_header(self):
        h_layout = QtWidgets.QHBoxLayout()
        workspace_gb = QtWidgets.QGroupBox('Workspaces')
        v_layout = QtWidgets.QVBoxLayout(workspace_gb)

        self._workspace_cb = QtWidgets.QComboBox()
        flag = QtWidgets.QAbstractItemView.DragOnly
        self._workspace_cb.view().setDragDropMode(flag)

        self._edit_btn = QtWidgets.QPushButton('Edit')
        self._edit_btn.setMaximumSize(QtCore.QSize(40, 23))
        self._edit_btn.setCheckable(True)

        v_layout.addWidget(self._workspace_cb)
        h_layout.addWidget(workspace_gb)
        h_layout.addStretch()
        h_layout.addWidget(self._edit_btn)
        return h_layout

    def _setup_edit_options(self):
        add_del_l = QtWidgets.QHBoxLayout()

        self._add_btn = QtWidgets.QPushButton('Add')
        self._add_btn.setMaximumSize(QtCore.QSize(60, 23))
        add_menu = QtWidgets.QMenu(self)
        add_menu.addAction('Workspace', self._add_workspace)
        add_menu.addAction('App or File', self._add_app)
        self._add_btn.setMenu(add_menu)

        self._del_btn = Delete_Btn(self)
        self._del_btn.setText('Delete')
        self._del_btn.setAcceptDrops(True)
        self._del_btn.setIcon(self._icons.icon(self._icons.Trashcan))
        self._del_btn.setIconSize(QtCore.QSize(32, 32))
        self._del_btn.setFlat(True)

        add_del_l.addWidget(self._add_btn)
        add_del_l.addWidget(self._del_btn)
        return add_del_l

    def _setup_apps(self):
        self._app_lw = QtWidgets.QListWidget()
        self._app_lw.setAlternatingRowColors(True)
        flag = QtWidgets.QAbstractItemView.InternalMove
        self._app_lw.setDragDropMode(flag)
        return self._app_lw

    def _setup_tray_icon(self):
        tray_icon = QtWidgets.QSystemTrayIcon(self)
        tray_icon.setIcon(self._tpl_icon)
        tray_icon.setToolTip('Applications Workbench')

        tray_menu = QtWidgets.QMenu(self)
        tray_menu.addAction('Open', self.show)
        tray_menu.addAction('GitHub', self._workbench_launcher.external_link)
        tray_menu.addSeparator()
        q = QtWidgets.QAction('Quit', self, triggered=self._close)
        tray_menu.addAction(q)
        tray_icon.setContextMenu(tray_menu)
        tray_icon.show()

    def _setup_connections(self):
        ws = self._workspace_changed
        self._workspace_cb.currentIndexChanged.connect(ws)
        self._edit_btn.clicked.connect(self._edit_toggle)
        dw = self._dragging_workspace
        self._workspace_cb.view().pressed.connect(dw)
        self._app_lw.itemPressed.connect(self._dragging_app)

    # ======= DISPLAY =================================

    def _populate_workspaces(self):
        ws = self._workspace_changed
        self._workspace_cb.currentIndexChanged.disconnect(ws)
        self._workspace_cb.clear()
        self._workspace_cb.addItems(self._workbench_launcher.get_workspaces())
        self._workspace_cb.currentIndexChanged.connect(ws)
        self._populate_apps()

    def _populate_apps(self):
        self._app_lw.clear()
        ws = self.get_workspace()
        for app_name in self._workbench_launcher.get_app_names(ws):
            item = QtWidgets.QListWidgetItem(self._app_lw)
            icon = self._workbench_launcher.get_app_icon(ws, app_name)
            if icon:
                item.setIcon(QtGui.QIcon(icon))
            else:
                item.setIcon(self._icons.icon(self._icons.File))
            item.setText(app_name)

    def closeEvent(self, e):
        self.hide()
        e.ignore()

    def _close(self):
        self._save_settings()
        QtWidgets.QApplication.instance().quit()

    # ------------ WORKSPACE ------------

    def get_workspace(self):
        ''' Returns the currently selection workspace from combobox. '''
        return str(self._workspace_cb.currentText())

    def _workspace_changed(self):
        self._populate_apps()
        self._save_settings()

    def _run_app(self, item):
        item.setSelected(False)
        self._workbench_launcher.run_app(self.get_workspace(), str(item.text()))

    # ------------ EDIT MODE ------------

    def _edit_toggle(self):
        self._edit_op[self._edit_btn.isChecked()]()
        self._app_lw.setDragEnabled(self._edit_btn.isChecked())
        self._add_btn.setVisible(self._edit_btn.isChecked())
        self._del_btn.setVisible(self._edit_btn.isChecked())
        self._save_settings()

    def _edit_on(self):
        self._app_lw.itemClicked.disconnect(self._run_app)
        self._edit_btn.setText('Done')

    def _edit_off(self):
        self._app_lw.itemClicked.connect(self._run_app)
        self._edit_btn.setText('Edit')

    # ------------ ADD ------------

    def _add_workspace(self):
        ws = 'New WORKSPACE'
        msg = 'Please enter a name for your workspace.'
        text = QtWidgets.QInputDialog.getText(self, ws, msg)[0]
        if text:
            self._workbench_launcher.add_workspace(str(text))
            self._populate_workspaces()
            index = self._workspace_cb.findText(text)
            self._workspace_cb.setCurrentIndex(index)
            self._save_settings()

    def _add_app(self):
        if self._app_instruction:
            msg = '1) Select program, file or shortcut\n'
            msg += '2) Select an icon image (Optional)'
            QtWidgets.QMessageBox.information(self, 'Add Program', msg)
            self._app_instruction = False
        sel = 'Select a file/program'
        app = self._file_dialogs[QT_VER](sel, self._my_path)
        if app:
            path = os.path.split(app)[0]
            msg = 'Select .ICO file for icon (optional)'
            icon = self._file_dialogs[QT_VER](msg, path)
            self._workbench_launcher.add_app(self.get_workspace(), app, icon)
            self._populate_apps()
            self._save_settings()

    def _file_dialog(self, msg, path):
        return QtWidgets.QFileDialog.getOpenFileName(self, msg, path)[0]

    def _file_dialog_pyqt4(self, msg, path):
        fd = QtWidgets.QFileDialog.getOpenFileName(self, msg, path)
        return str(fd)

    # ------------ DELETE ------------

    def _dragging_workspace(self, index):
        ws = str(self._workspace_cb.itemText(index.row()))
        self._dragging = ('workspace', ws)

    def _dragging_app(self, item):
        self._dragging = ('application', str(item.text()))

    def _delete_app(self, app_name):
        self._workbench_launcher.delete_app(self.get_workspace(), app_name)
        self._populate_apps()

    def _delete_workspace(self, ws_name):
        self._workbench_launcher.delete_workspace(ws_name)
        self._populate_workspaces()

    def delete_item(self):
        ''' Delete the item dragged onto Delete button '''
        typ = self._dragging[0]
        name = self._dragging[1]
        title = f'Delete {typ}?'
        msg = f'Are you sure you want to delete {typ} "{name}"'
        no = QtWidgets.QMessageBox.No
        yes = QtWidgets.QMessageBox.Yes
        btn = QtWidgets.QMessageBox.warning(self, title, msg, yes, no)
        if btn == yes:
            self._delete_op[typ](name)
            self._save_settings()

    # ------------ SETTINGS ------------

    def _save_settings(self):
        c = self._app_lw.count()
        names = [self._app_lw.item(i).text() for i in range(c)]
        ws = self.get_workspace()
        self._workbench_launcher.reorder_apps(ws, names)
        self._settings.setValue('CurrentWorkspace', ws)
        self._workbench_launcher.write_json_file(self._json_file)
        self._settings.setValue('PosX', int(self.x()))
        self._settings.setValue('PosY', int(self.y()))

    def _load_settings(self):
        if 'CurrentWorkspace' in self._settings.allKeys() and \
                os.path.exists(self._json_file):
            x, y, cws = self._settings_op[PY_VER][QT_VER]()
            self._workbench_launcher.read_json_file(self._json_file)
            self._populate_workspaces()
            index = self._workspace_cb.findText(cws)
            self._workspace_cb.setCurrentIndex(index)
            self.move(x, y)
        else:
            self._workbench_launcher.add_workspace('Default')
            self._populate_workspaces()

    def _get_settings(self):
        x = int(self._settings.value('PosX'))
        y = int(self._settings.value('PosY'))
        cws = str(self._settings.value('CurrentWorkspace'))
        return x, y, cws


if __name__ == '__main__':
    print(PY_VER)
    print(QT_VER)
    app = QtWidgets.QApplication(sys.argv)
    if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
        QtWidgets.QMessageBox.critical(
            None, 'Error!',
            'No system tray available for this system! Exiting...'
        )
        sys.exit(1)
    QtWidgets.QApplication.setQuitOnLastWindowClosed(False)
    ex = Workbench_Launcher_GUI()
    ex.show()
    sys.exit(app.exec_())

# github.com/eabdiel
