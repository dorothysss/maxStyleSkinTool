"""
===================================================================================================================
run this script directly or source in the script and run maxStyleSkinTool.dialog.maxStyleWeightDialog.show_dialog()
===================================================================================================================
"""

from PySide2 import QtCore, QtWidgets
from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui
import maya.cmds as cmds
import maya.mel as mel
import pymel.core as pm
import re


def maya_main_window():
    # get maya mainwindow so our dialog could be attached to it
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
        # remove question mark(help button)
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

        # TODO use selectionChange callback instead of button
        self.getWeighting_btn = QtWidgets.QPushButton("Get selected verts weighting")

        self.boneInSelected_label = QtWidgets.QLabel("All weighted Bones in Selected Verts:")
        self.boneInSelected_label2 = QtWidgets.QLabel(
            "(if more than one verts are selected, weight only represent the 1st vert.)")
        self.boneInSelectedVerts_table = QtWidgets.QTableWidget()
        self.boneInSelectedVerts_table.setColumnCount(2)
        self.boneInSelectedVerts_table.setHorizontalHeaderLabels(["Bone Name", "Weight"])
        self.boneInSelectedVerts_table.setColumnWidth(0, 250)
        self.boneInSelectedVerts_table.setColumnWidth(1, 50)
        tableHeader = self.boneInSelectedVerts_table.horizontalHeader()
        tableHeader.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        self.statusBar = QtWidgets.QStatusBar()

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
        main_layout.addWidget(self.getWeighting_btn)
        main_layout.addLayout(weightButtonLayout)
        main_layout.addLayout(utilBottonLayout)
        main_layout.addWidget(self.boneInSelected_label)
        main_layout.addWidget(self.boneInSelected_label2)
        main_layout.addWidget(self.boneInSelectedVerts_table)
        main_layout.addWidget(self.statusBar)

    def create_connections(self):
        self.editSkin_btn.toggled.connect(self.check_editBtn_status)
        self.getWeighting_btn.clicked.connect(self.getWeighting_btn_clicked)
        self.weight0_btn.clicked.connect(lambda: self.weight_btn_clicked(0))
        self.weight01_btn.clicked.connect(lambda: self.weight_btn_clicked(0.1))
        self.weight025_btn.clicked.connect(lambda: self.weight_btn_clicked(0.25))
        self.weight05_btn.clicked.connect(lambda: self.weight_btn_clicked(0.5))
        self.weight075_btn.clicked.connect(lambda: self.weight_btn_clicked(0.75))
        self.weight09_btn.clicked.connect(lambda: self.weight_btn_clicked(0.9))
        self.weight1_btn.clicked.connect(lambda: self.weight_btn_clicked(1.0))

    def check_editBtn_status(self):
        btnStatus = self.editSkin_btn.isChecked()
        selectedModel = self.get_selectedModel()
        if btnStatus:
            # TODO check when selection mode is not in object
            self.edit_skin_checked()
            pm.mel.doMenuComponentSelection(selectedModel, "puv")
        else:
            # TODO check when selection mode is not in object
            self.edit_skin_unchecked()
            pm.mel.maintainActiveChangeSelectMode(selectedModel, 0)

    def edit_skin_checked(self):
        self.statusBar.clearMessage()
        self.refresh_boneInSkin_list()
        # TODO use selectionChange callback so boneInSelectedVerts_table updates here
        # self.refresh_boneInSelectedVerts_table()

    def edit_skin_unchecked(self):
        self.statusBar.clearMessage()
        self.clear_boneInSkin_list()
        self.clear_boneInSelectedVerts_table()

    def getWeighting_btn_clicked(self):
        selectedModel = self.get_selectedModel()
        pm.mel.doMenuComponentSelection(selectedModel, "puv")

        selectedUV = self.get_selected_uv()

        selectedUVToVert = self.get_selected_uv_to_verts()
        selectedSkinCluster = self.get_skinClusterFromModel(selectedModel)

        (weightedBones, boneWeight) = self.get_boneAndWeight_from_verts(selectedSkinCluster, selectedUVToVert)
        self.refresh_boneInSelectedVerts_table(weightedBones, boneWeight)

        #pm.mel.doMenuComponentSelection(selectedModel, "puv")
        #cmds.select(cl=True)
        cmds.select(selectedUV)
        self.statusBar.showMessage("{num} of verts selected".format(num=len(selectedUVToVert)))

    def get_selected_uv(self):
        selectedUV = cmds.filterExpand(ex=True, sm=35)
        return selectedUV

    def get_selected_uv_to_verts(self):
        selectedUV = cmds.filterExpand(ex=True, sm=35)
        # convert uv selection to vert selection instead of using vert selection
        selectedUVToVerts = cmds.polyListComponentConversion(selectedUV, tv=True)
        return selectedUVToVerts

    def get_boneAndWeight_from_verts(self, selectedSkinCluster, selectedVerts):
        weightedBoneList = []
        singleVertList = self.make_single_vert_list(selectedVerts)
        if len(singleVertList) > 0:
            # only show 1st vert's weight value if more than 1 verts are selected
            cmds.select(singleVertList[0])
            boneWeightOn1stVert = cmds.skinPercent(selectedSkinCluster, singleVertList[0], query=True, value=True)
            shownWeightList = []
            fullBoneList = self.get_boneList_from_skinCluster(selectedSkinCluster)
            for i in range(len(singleVertList)):
                cmds.select(singleVertList[i])
                vertIWeightList = cmds.skinPercent(selectedSkinCluster, singleVertList[i], query=True, value=True)
                for j in range(len(vertIWeightList)):
                    # TODO add user input for threshhold 0.01
                    if vertIWeightList[j] > 0.01:
                        if fullBoneList[j] not in weightedBoneList:
                            weightedBoneList.append(fullBoneList[j])
                            if boneWeightOn1stVert[j] != 0.0:
                                shownWeightList.append(str(boneWeightOn1stVert[j]))
                            else:
                                shownWeightList.append('0.0')
        return weightedBoneList, shownWeightList

    def make_single_vert_list(self,selectedVerts):
        fullSingleVertList = []
        if len(selectedVerts)>0:
            for i in range(len(selectedVerts)):
                if ':' in selectedVerts[i]:
                    singleVerList = self.get_single_vert_from_multiple(selectedVerts[i])
                    for j in range(len(singleVerList)):
                        fullSingleVertList.append(singleVerList[j])
                else:
                    fullSingleVertList.append(selectedVerts[i])
        return fullSingleVertList

    def get_single_vert_from_multiple(self, multipleVerts):
        #multiple verts is something like 'testMesh.vtx[8162:8163]'
        #return a list like ['testMesh.vtx[8162]','testMesh.vtx[8163]']
        singleVertsList = []

        strPrefix = multipleVerts.split('[')
        # result: 'testMesh.vtx'

        # getting numbers from string
        temp = re.findall(r'\d+', multipleVerts)
        numbers = list(map(int, temp))

        for i in range(numbers[0], (numbers[1]+1)):
            singleVert = strPrefix[0] + '[' + str(i) + ']'
            singleVertsList.append(singleVert)

        return singleVertsList

    def refresh_boneInSelectedVerts_table(self, weightedBone, boneWeight):
        self.boneInSelectedVerts_table.setRowCount(0)
        for i in range(len(weightedBone)):
            self.boneInSelectedVerts_table.insertRow(i)
            self.insert_tableItem(i, 0, weightedBone[i])
            self.insert_tableItem(i, 1, boneWeight[i])
            self.boneInSelectedVerts_table.setRowHeight(i, 1)

    def insert_tableItem(self, row, column, boneName):
        item = QtWidgets.QTableWidgetItem(boneName)
        #get rid of Editable
        item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        self.boneInSelectedVerts_table.setItem(row, column, item)

    def weight_btn_clicked(self, weightValue):
        self.statusBar.clearMessage()
        selectedBone = ''
        #TODO list and table widgt can only have 1 selection
        selectedRow = self.boneInSelectedVerts_table.currentRow()
        if selectedRow != -1:
            selectedBone = self.boneInSelectedVerts_table.item(selectedRow, 0).text()
        else:
            self.statusBar.showMessage('please select a bone to change weight')

        selectedUVToVerts = self.get_selected_uv_to_verts()
        singleVertList = self.make_single_vert_list(selectedUVToVerts)
        selectedSkinCluster = self.get_skinCLusterFromUVSelection(selectedUVToVerts)

        if len(singleVertList) > 0:
            cmds.select(singleVertList[0])
            boneWeightOn1stVert = cmds.skinPercent(selectedSkinCluster, singleVertList[0], query=True, value=True)

    def set_weight_with_bone(self, selectedBone, selectedUV):
        pass

    def uvSelectToUvShell(self):
        mel.eval('SelectUVShell')

    def get_skinCLusterFromUVSelection(self,selectedUV):
        selectedSkinCluster = ''
        if len(selectedUV)>0:
            selectedModel = selectedUV[0].split('.')[0]
            selectedSkinCluster = self.get_skinClusterFromModel(selectedModel)
        return selectedSkinCluster

    def refresh_boneInSkin_list(self):
        self.statusBar.clearMessage()
        self.boneInSkin_list.clear()
        selectedModel = self.get_selectedModel()
        selectedSkinCluster = self.get_skinClusterFromModel(selectedModel)
        boneList = self.get_boneList_from_skinCluster(selectedSkinCluster)
        if len(boneList) > 0:
            for i in range(len(boneList)):
                self.boneInSkin_list.addItem(boneList[i])
        else:
            self.statusBar.showMessage("Please select a model with skin cluster")

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

    def get_skinClusterFromModel(self, model):
        selectedSkinCluster = []
        if len(model) > 0:
            selectedSkinCluster = mel.eval('findRelatedSkinCluster ' + model)
        return selectedSkinCluster

    def get_boneList_from_skinCluster(self, selectedSkinCluster):
        boneList = []
        if len(selectedSkinCluster) > 0:
            boneList = cmds.skinCluster(selectedSkinCluster, query=True, inf=True)
        return boneList

    def clear_boneInSkin_list(self):
        self.boneInSkin_list.clear()

    def get_selectedVerts(self):
        selection = cmds.ls(sl=True)
        selectedVerts = cmds.filterExpand(selection, sm=31)
        return selectedVerts

    def clear_boneInSelectedVerts_table(self):
        self.boneInSelectedVerts_table.setRowCount(0)

    def closeEvent(self, event):
        print('closeEvent')


if __name__ == "__main__":
    try:
        maxStyleWeight.close()
        maxStyleWeight.deleteLater()
    except:
        pass

    maxStyleWeight = maxStyleWeightDialog()
    maxStyleWeight.show()
