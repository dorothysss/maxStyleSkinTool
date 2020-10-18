"""
===================================================================================================================
run this script directly or source in the script and run maxStyleSkinTool.dialog.maxStyleWeightDialog.show_dialog()

strugglesheng@gmail.com
===================================================================================================================
"""

from PySide2 import QtCore, QtWidgets
from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui
import maya.cmds as cmds
import maya.mel as mel
import pymel.core as pm
import re
from maya import OpenMaya




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

        mel.eval("""if(!`exists doMenuComponentSelection`) eval("source dagMenuProc");""")

        self.setWindowTitle("3ds Max Style Weighting Tool")
        self.setMinimumWidth(200)
        self.setMaximumWidth(400)
        self.setMinimumHeight(600)
        # remove question mark(help button)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

        self.callBack_selectionChange = OpenMaya.MEventMessage.addEventCallback("SelectionChanged",
                                                                                self.maya_selection_changed)

    # selection change call back function for select uv to uv shell
    def maya_selection_changed(self, *args, **kwargs):
        if self.element_cbx.isChecked():
            selectedUV = self.get_selected_uv()
            if selectedUV:
                self.uvSelectToUvShell()

    def create_widgets(self):
        self.editSkin_btn = QtWidgets.QPushButton("Edit Skin")
        self.editSkin_btn.setCheckable(True)
        self.element_cbx = QtWidgets.QCheckBox("Select Element")
        self.resumeMesh_btn = QtWidgets.QPushButton("Resume mesh after bone transform change")

        self.weight0_btn = QtWidgets.QPushButton("0")
        self.weight01_btn = QtWidgets.QPushButton("0.1")
        self.weight025_btn = QtWidgets.QPushButton("0.25")
        self.weight05_btn = QtWidgets.QPushButton("0.5")
        self.weight075_btn = QtWidgets.QPushButton("0.75")
        self.weight09_btn = QtWidgets.QPushButton("0.9")
        self.weight1_btn = QtWidgets.QPushButton("1")

        # self.copy_btn = QtWidgets.QPushButton("Copy")
        # self.paste_btn = QtWidgets.QPushButton("Paste")

        # TODO use selectionChange callback instead of button(slow)
        self.getWeighting_btn = QtWidgets.QPushButton("Get selected verts weighting")

        self.boneInSelected_label = QtWidgets.QLabel(
            "List all bones in skincluster, grey means unused on selected verts")
        self.boneInSelected_label2 = QtWidgets.QLabel(
            "(If more than one verts are selected, weight only represent the 1st vert.)")
        self.boneAndWeight_table = QtWidgets.QTableWidget()
        self.boneAndWeight_table.setColumnCount(2)
        self.boneAndWeight_table.setHorizontalHeaderLabels(["Bone Name", "Weight"])
        self.boneAndWeight_table.setColumnWidth(0, 250)
        self.boneAndWeight_table.setColumnWidth(1, 50)
        tableHeader = self.boneAndWeight_table.horizontalHeader()
        tableHeader.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        self.statusBar = QtWidgets.QStatusBar()

    def create_layouts(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        main_layout.addWidget(self.editSkin_btn)
        main_layout.addWidget(self.resumeMesh_btn)
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

        main_layout.addWidget(self.getWeighting_btn)
        main_layout.addLayout(weightButtonLayout)
        main_layout.addLayout(utilBottonLayout)
        main_layout.addWidget(self.boneInSelected_label)
        main_layout.addWidget(self.boneInSelected_label2)
        main_layout.addWidget(self.boneAndWeight_table)
        main_layout.addWidget(self.statusBar)

    def create_connections(self):
        self.editSkin_btn.toggled.connect(self.check_editBtn_status)
        self.resumeMesh_btn.clicked.connect(self.resume_mesh_clicked)
        self.getWeighting_btn.clicked.connect(self.refresh_boneAndWeight_table_boneAndWeight)
        self.weight0_btn.clicked.connect(lambda: self.weight_btn_clicked(0))
        self.weight01_btn.clicked.connect(lambda: self.weight_btn_clicked(0.1))
        self.weight025_btn.clicked.connect(lambda: self.weight_btn_clicked(0.25))
        self.weight05_btn.clicked.connect(lambda: self.weight_btn_clicked(0.5))
        self.weight075_btn.clicked.connect(lambda: self.weight_btn_clicked(0.75))
        self.weight09_btn.clicked.connect(lambda: self.weight_btn_clicked(0.9))
        self.weight1_btn.clicked.connect(lambda: self.weight_btn_clicked(1.0))
        # self.copy_btn.clicked.connct(self.copy_weighting())
        # self.paste_btn.clicked.connect(self.paste_weight())

    def check_editBtn_status(self):
        btnStatus = self.editSkin_btn.isChecked()
        selectedModel = self.get_selectedModel()
        if btnStatus:
            # TODO check when selection mode is not in object
            self.edit_skin_checked()
            # pm.mel.doMenuComponentSelection(selectedModel, "puv")
        else:
            # TODO check when selection mode is not in object
            self.edit_skin_unchecked()
            pm.mel.maintainActiveChangeSelectMode(selectedModel, 0)

    def edit_skin_checked(self):
        self.statusBar.clearMessage()
        self.refresh_boneAndWeight_table_bonesOnly()

    def edit_skin_unchecked(self):
        self.statusBar.clearMessage()
        self.clear_boneAndWeight_table()

    def resume_mesh_clicked(self):
        selectedModel = self.get_selectedModel()
        selectedSkinCluster = self.get_skinClusterFromModel(selectedModel)
        print(selectedSkinCluster)
        if selectedSkinCluster:
            boneList = self.get_boneList_from_skinCluster(selectedSkinCluster)
            mel.eval("""doDetachSkin "2" {"2", "0"}""")
            cmds.select(boneList)
            cmds.select(selectedModel, add=True)
            cmds.skinCluster()
        else:
            self.statusBar.showMessage("Select a model with skinCluster")

    def refresh_boneAndWeight_table_bonesOnly(self):
        self.boneAndWeight_table.setRowCount(0)
        self.statusBar.clearMessage()
        selectedModel = self.get_selectedModel()
        selectedSkinCluster = self.get_skinClusterFromModel(selectedModel)
        boneList = self.get_boneList_from_skinCluster(selectedSkinCluster)
        if boneList:
            for i in range(len(boneList)):
                self.boneAndWeight_table.insertRow(i)
                self.insert_tableItem(i, 0, boneList[i])
                self.boneAndWeight_table.setRowHeight(i, 1)
            pm.mel.doMenuComponentSelection(selectedModel, "puv")
        else:
            self.statusBar.showMessage("Please select a model with skin cluster")
            # self.editSkin_btn.setChecked(False)

    def refresh_boneAndWeight_table_boneAndWeight(self):
        self.boneAndWeight_table.setRowCount(0)
        selectedModel = self.get_selectedModel()
        pm.mel.doMenuComponentSelection(selectedModel, "puv")

        selectedUV = self.get_selected_uv()

        selectedUVToVert = self.get_selected_uv_to_verts()
        selectedSingleVerts = self.get_single_vert_list(selectedUVToVert)
        selectedSkinCluster = self.get_skinClusterFromModel(selectedModel)
        boneInSkinCluster = self.get_boneList_from_skinCluster(selectedSkinCluster)

        if selectedSingleVerts and selectedSkinCluster:
            (weightedBones, boneWeightOn1stVert) = self.get_boneAndWeight_from_verts(selectedSkinCluster,
                                                                                     selectedSingleVerts)
            boneCountOn1stVert = len(boneWeightOn1stVert)

            for i in range(len(weightedBones)):
                self.boneAndWeight_table.insertRow(i)
                self.insert_tableItem(i, 0, weightedBones[i])
                if i < boneCountOn1stVert:
                    self.insert_tableItem(i, 1, boneWeightOn1stVert[i])
                self.boneAndWeight_table.setRowHeight(i, 1)

            for w in weightedBones:
                if w in boneInSkinCluster:
                    boneInSkinCluster.remove(w)

            # only not weighted bones are left
            currentRowCount = self.boneAndWeight_table.rowCount()
            for i in range(len(boneInSkinCluster)):
                self.boneAndWeight_table.insertRow(currentRowCount + i)
                self.insert_tableItem(currentRowCount + i, 0, boneInSkinCluster[i], False)
                self.boneAndWeight_table.setRowHeight(currentRowCount + i, 1)

            self.statusBar.showMessage("{num} verts selected".format(num=len(selectedSingleVerts)))
            cmds.select(selectedUV)
        else:
            self.statusBar.showMessage('select some points')

    def insert_tableItem(self, row, column, boneName, weighted=True):
        item = QtWidgets.QTableWidgetItem(str(boneName))
        # get rid of Editable
        item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        self.boneAndWeight_table.setItem(row, column, item)
        if not weighted:
            item.setBackgroundColor('grey')

    def get_selected_uv(self):
        selectedUV = cmds.filterExpand(ex=True, sm=35)
        if selectedUV == None:
            selectedUV = ''
        return selectedUV

    def get_selected_uv_to_verts(self):
        selectedUV = cmds.filterExpand(ex=True, sm=35)
        # convert uv selection to vert selection instead of using vert selection
        selectedUVToVerts = cmds.polyListComponentConversion(selectedUV, tv=True)
        return selectedUVToVerts

    def get_boneAndWeight_from_verts(self, selectedSkinCluster, selectedVerts):
        shownWeightList = []
        showBoneList = []
        fullBoneList = self.get_boneList_from_skinCluster(selectedSkinCluster)
        # singleVertList = self.make_single_vert_list(selectedVerts)
        if selectedVerts:
            # only show 1st vert's weight value if more than 1 verts are selected
            cmds.select(selectedVerts[0])
            boneWeightOn1stVert = cmds.skinPercent(selectedSkinCluster, selectedVerts[0], query=True, value=True)
            if boneWeightOn1stVert:
                for i in range(len(boneWeightOn1stVert)):
                    if boneWeightOn1stVert[i] > 0.01:
                        shownWeightList.append(boneWeightOn1stVert[i])
                        showBoneList.append(fullBoneList[i])

            for i in range(1, len(selectedVerts)):
                cmds.select(selectedVerts[i])
                vertIWeightList = cmds.skinPercent(selectedSkinCluster, selectedVerts[i], query=True, value=True)
                for j in range(len(vertIWeightList)):
                    # TODO add user input for threshhold 0.01
                    if vertIWeightList[j] > 0.01:
                        if fullBoneList[j] not in showBoneList:
                            showBoneList.append(fullBoneList[j])
        return showBoneList, shownWeightList

    def get_single_vert_list(self, selectedVerts):
        fullSingleVertList = []
        if selectedVerts:
            for s in selectedVerts:
                if ':' in s:
                    singleVerList = self.split_multiple_verts(s)
                    fullSingleVertList.extend(singleVerList)
                else:
                    fullSingleVertList.append(s)
        return fullSingleVertList

    def split_multiple_verts(self, multipleVerts):
        # multiple verts is something like 'testMesh.vtx[8162:8163]'
        # return a list like ['testMesh.vtx[8162]','testMesh.vtx[8163]']
        singleVertsList = []
        if multipleVerts:
            strPrefix = multipleVerts.split('[')
            # result: 'testMesh.vtx'

            # getting numbers from string
            temp = re.findall(r'\d+', strPrefix[1])
            numbers = list(map(int, temp))

            for i in range(numbers[0], (numbers[1] + 1)):
                singleVert = strPrefix[0] + '[' + str(i) + ']'
                singleVertsList.append(singleVert)

        return singleVertsList

    def weight_btn_clicked(self, weightValue):
        self.statusBar.clearMessage()
        selectedBone = ''
        selectedRow = self.boneAndWeight_table.currentRow()
        if selectedRow != -1:
            selectedBone = self.boneAndWeight_table.item(selectedRow, 0).text()
        else:
            self.statusBar.showMessage('please select a bone to change weight')

        selectedUV = self.get_selected_uv()
        selectedUVToVerts = self.get_selected_uv_to_verts()
        singleVertList = self.get_single_vert_list(selectedUVToVerts)
        selectedSkinCluster = self.get_skinCLusterFromUVSelection(selectedUVToVerts)

        if singleVertList:
            cmds.select(cl=True)
            for s in singleVertList:
                cmds.select(s)
                cmds.skinPercent(selectedSkinCluster, s, transformValue=[(selectedBone, weightValue)])

        cmds.select(selectedUV)
        self.refresh_boneAndWeight_table_boneAndWeight()

    def uvSelectToUvShell(self):
        mel.eval('SelectUVShell')

    def get_skinCLusterFromUVSelection(self, selectedUV):
        selectedSkinCluster = ''
        if selectedUV:
            selectedModel = selectedUV[0].split('.')[0]
            selectedSkinCluster = self.get_skinClusterFromModel(selectedModel)
        return selectedSkinCluster

    def get_selectedModel(self):
        selectedModel = []
        selection = cmds.ls(objectsOnly=True, sl=True)
        if selection:
            if cmds.objectType(selection[0]) == 'transform':
                selectedModel = selection[0]
            else:
                selectedObj = (cmds.listRelatives(selection[0], allParents=True))[0]
                if cmds.objExists(selectedObj):
                    selectedModel = selectedObj
        return selectedModel

    def get_skinClusterFromModel(self, model):
        returnSkinCluster = []
        if model:
            selectedSkinCluster = mel.eval('findRelatedSkinCluster ' + model)
            if selectedSkinCluster:
                returnSkinCluster = selectedSkinCluster
        return returnSkinCluster

    def get_boneList_from_skinCluster(self, selectedSkinCluster):
        returnBoneList = []
        if selectedSkinCluster:
            boneList = cmds.skinCluster(selectedSkinCluster, query=True, inf=True)
            if boneList:
                returnBoneList = boneList
        return returnBoneList

    def get_selectedVerts(self):
        selection = cmds.ls(sl=True)
        selectedVerts = cmds.filterExpand(selection, sm=31)
        return selectedVerts

    def clear_boneAndWeight_table(self):
        self.boneAndWeight_table.setRowCount(0)

    def hideEvent(self, event):
        OpenMaya.MMessage.removeCallback(self.callBack_selectionChange)


if __name__ == "__main__":
    try:
        maxStyleWeight.close()
        maxStyleWeight.deleteLater()
    except:
        pass

    maxStyleWeight = maxStyleWeightDialog()
    maxStyleWeight.show()
