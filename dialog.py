from PySide2 import QtCore, QtWidgets
from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui
import maya.cmds as cmds
import maya.mel as mel
import pymel.core as pm


def maya_main_window():
	#get maya mainwindow so our dialog could be attached to it
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)


class maxStyleWeightDialog(QtWidgets.QDialog):
    dialog_instance = None

    @classmethod
    def show_dialog(cls):
        if not cls.dialog_instance:
            cls.dialog_instance = maxStyleWeightDialog()
        if cls.dialog_instance.isHidden():
            cls.dialog_instance.show()
        else:
            cls.dialog_instance.raise_()
            cls.dialog_instance.activateWindow()

    def __init__(self, parent=maya_main_window()):
        super(maxStyleWeightDialog, self).__init__(parent)

        self.setWindowTitle("3ds Max Style Weighting Tool")
        self.setMinimumWidth(200)
        self.setMaximumWidth(400)
        #remove question mark(help button)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.create_widgets()
        self.create_layouts()
        self.create_connections()


    def create_widgets(self):
        self.editSkin_btn = QtWidgets.QPushButton("Edit Skin")
        self.editSkin_btn.setCheckable(True)
        self.element_cbx = QtWidgets.QCheckBox("Select Element")
        self.boneInSkin_label = QtWidgets.QLabel("Bones in Skin Cluster:")
        # TODO self.line1 = QtWidgets.QGraphicsLineItem()
        self.boneInSkin_list = QtWidgets.QListWidget()
        self.boneInSkin_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.weight0_btn = QtWidgets.QPushButton("0")
        self.weight01_btn = QtWidgets.QPushButton("0.1")
        self.weight025_btn = QtWidgets.QPushButton("0.25")
        self.weight05_btn = QtWidgets.QPushButton("0.5")
        self.weight075_btn = QtWidgets.QPushButton("0.75")
        self.weight09_btn = QtWidgets.QPushButton("0.9")
        self.weight1_btn = QtWidgets.QPushButton("1")

        self.copy_btn = QtWidgets.QPushButton("Copy")
        self.paste_btn = QtWidgets.QPushButton("Paste")
        self.boneInSelected_label = QtWidgets.QLabel("All weighted Bones in Selected Verts:")
        self.boneInSelectedVerts_table = QtWidgets.QTableWidget()
        self.boneInSelectedVerts_table.setColumnCount(2)
        self.boneInSelectedVerts_table.setHorizontalHeaderLabels(["Bone Name","Weight"])
        self.boneInSelectedVerts_table.setColumnWidth(0,300)
        self.boneInSelectedVerts_table.setColumnWidth(1,50)
        tableHeader = self.boneInSelectedVerts_table.horizontalHeader()
        tableHeader.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)


    def create_layouts(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.editSkin_btn)
        main_layout.addWidget(self.element_cbx)

        weightButtonLayout = QtWidgets.QHBoxLayout()
        weightButtonLayout.addWidget(self.weight0_btn)
        weightButtonLayout.addWidget(self.weight01_btn)
        weightButtonLayout.addWidget(self.weight025_btn)
        weightButtonLayout.addWidget(self.weight05_btn)
        weightButtonLayout.addWidget(self.weight075_btn)
        weightButtonLayout.addWidget(self.weight09_btn)
        weightButtonLayout.addWidget(self.weight1_btn)

        utilBottonLayout = QtWidgets.QHBoxLayout()
        utilBottonLayout.addWidget(self.copy_btn)
        utilBottonLayout.addWidget(self.paste_btn)

        main_layout.addWidget(self.boneInSkin_label)
        main_layout.addWidget(self.boneInSkin_list)

        # TODO main_layout.addWidget(self.line1)
        main_layout.addLayout(weightButtonLayout)
        main_layout.addLayout(utilBottonLayout)
        main_layout.addWidget(self.boneInSelected_label)
        main_layout.addWidget(self.boneInSelectedVerts_table)

    def create_connections(self):
        self.editSkin_btn.toggled.connect(self.check_editBtn_status)
        self.weight0_btn.clicked.connect(self.refresh_boneInSkin_list)
        self.weight01_btn.clicked.connect(self.set_weight_value)
        self.weight025_btn.clicked.connect(self.set_weight_value)

    def check_editBtn_status(self):
        btnStatus = self.editSkin_btn.isChecked()
        selectedModel = self.get_selectedModel()
        if btnStatus:
            #TODO check whether selection = None
            self.edit_skin()
            pm.mel.doMenuComponentSelectionExt(selectedModel, "vertex", 0)
        else:
            #TODO check whether selection = None
            self.quit_edit_skin()
            pm.mel.maintainActiveChangeSelectMode(selectedModel, 0)

    def edit_skin(self):
        self.refresh_boneInSkin_list()
        self.refresh_boneInSelectedVerts_table()
        
    def quit_edit_skin(self):
        self.clear_boneInSkin_list()
        self.clear_boneInSelectedVerts_table()

    def set_weight_value(self, value):
        print(value)

    def refresh_boneInSkin_list(self):
        self.boneInSkin_list.clear()
        selectedModel = self.get_selectedModel()
        boneList = self.get_boneListFromModel(selectedModel)
        if len(boneList) > 0:
            for i in range(len(boneList)):
                self.boneInSkin_list.addItem(boneList[i])
        else:
            print("please select a model with skin cluster")

    def get_selectedModel(self):
        selectedModel = []
        selection = cmds.ls(objectsOnly=True, sl=True)
        if len(selection) > 0:
            if cmds.objectType(selection[0]) == 'transform':
                selectedModel = selection[0]
            else:
                selectedObj = (cmds.listRelatives(selection[0], allParents=True))[0]
                if cmds.objExists(selectedObj):
                    selectedModel = selectedObj
        return selectedModel

    def get_boneListFromModel(self, model):
        selectedSkinCluster = []
        boneList = []
        if len(model) > 0:
            selectedSkinCluster = mel.eval('findRelatedSkinCluster ' + model)

        if len(selectedSkinCluster) > 0:
            boneList=cmds.skinCluster(selectedSkinCluster, query=True, inf=True)
        return boneList

    def clear_boneInSkin_list(self):
        self.boneInSkin_list.clear()

    def refresh_boneInSelectedVerts_table(self):
        self.boneInSelectedVerts_table.setRowCount(0)
        selectedModel = self.get_selectedModel()
        boneList = self.get_boneListFromModel(selectedModel)
        for i in range(len(boneList)):
            self.boneInSelectedVerts_table.insertRow(i)
            self.insert_tableItem(i, 0, boneList[i])
            self.boneInSelectedVerts_table.setRowHeight(i, 1)

    def get_selectedVerts(self):
        selection = cmds.ls(sl=True)
        selectedVerts = cmds.filterExpand(selection, sm=31)
        return selectedVerts

    def get_selectedVertsBoneList(self):
        pass

    def insert_tableItem(self, row, column, boneName):
        item = QtWidgets.QTableWidgetItem(boneName)
        self.boneInSelectedVerts_table.setItem(row, column, item)

    def clear_boneInSelectedVerts_table(self):
        self.boneInSelectedVerts_table.setRowCount(0)


if __name__ == "__main__":
    try:
        maxStyleWeight.close()
        maxStyleWeight.deleteLater()
    except:
        pass

    maxStyleWeight = maxStyleWeightDialog()
    maxStyleWeight.show()