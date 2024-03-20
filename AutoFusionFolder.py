#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #######################################################
# AutoFusionFolder v0.9
# #######################################################
# Automatically generate Fusion folder structure for movies

# #######################################################
# Imports
# #######################################################

# Import pymxs
import pymxs  # type:ignore
import os
import json
import shutil
import re

# Import custom lib
import gblExternalVars as extVars  # type:ignore

# Import Qt
from PySide2 import QtWidgets, QtCore  # type:ignore
from PySideGui import QtInterfaces  # type:ignore
from PySideGui import QtSpecialsWidgets  # type:ignore

ms = pymxs.runtime


class AutoFusionFolder(QtInterfaces.BaseDialog):
    # AutoFusionFolder tool main class
    version = "v1.0"
    default_fusion_template_file_name = "TEMPLATE_FUSION_18_v1.comp"

    def __init__(self):
        # Init UI
        super().__init__(
            title="AutoFusionFolder",
            subtitle=f"{AutoFusionFolder.version} - Generate folder structure for Fusion files",
            ask="http://wiki/doku.php?id=softwares:autodesk:3dsmax:asytools_3dsmax:utilities:autofusionfolder",
            height=60
        )

    # #############################################################################
    # Define UI
    # #############################################################################

    def setContent(self):
        # Setup UI
        self.setSetupContent()

    def setSetupContent(self):
        # Get current project path
        project_path = extVars.Path.Project.root() or extVars.Path.Prod.asyConcept()

        # Default Fusion template
        asyFusion = extVars.Path.Tools.asyFusion()
        default_fusion_template_file = os.path.join(asyFusion, "Templates", AutoFusionFolder.default_fusion_template_file_name)

        # Define main UI
        self.setup_grp = QtSpecialsWidgets.simpleGroup(" Setup :")
        self.layout.addWidget(self.setup_grp)

        # Define project folder path selection
        self.folder_lbl = QtWidgets.QLabel("Project folder :")
        self.setup_grp.content.addWidget(self.folder_lbl, 0, 0, QtCore.Qt.AlignLeft)

        self.folder_path_line_edit = QtWidgets.QLineEdit(project_path)
        self.folder_path_line_edit.setFixedSize(420, 26)
        self.setup_grp.content.addWidget(self.folder_path_line_edit, 0, 1, QtCore.Qt.AlignLeft)
        self.folder_path_line_edit.textChanged.connect(self.on_folder_path_changed)

        # Define Fusion template checkbox
        self.fusion_chck = QtWidgets.QCheckBox("Use Fusion template:")
        self.fusion_chck.setChecked(True)
        self.setup_grp.content.addWidget(self.fusion_chck, 1, 0, QtCore.Qt.AlignLeft)
        self.fusion_chck.stateChanged.connect(self.on_fusion_chck_changed)

        # Define Fusion template file selection
        self.fusion_lbl = QtWidgets.QLabel("Fusion template file :")
        self.setup_grp.content.addWidget(self.fusion_lbl, 2, 0, QtCore.Qt.AlignLeft)

        self.fusion_path_line_edit = QtWidgets.QLineEdit(default_fusion_template_file)
        self.fusion_path_line_edit.setFixedSize(420, 26)
        self.setup_grp.content.addWidget(self.fusion_path_line_edit, 2, 1, QtCore.Qt.AlignLeft)
        self.fusion_path_line_edit.textChanged.connect(self.on_fusion_path_changed)

        # Define start script button
        self.start_btn = QtWidgets.QPushButton("Start")
        self.setup_grp.content.addWidget(self.start_btn, 3, 1, QtCore.Qt.AlignRight)
        self.start_btn.clicked.connect(self.on_clickstart_btn)

        # Initial values check
        self.on_folder_path_changed(self.folder_path_line_edit.text())
        self.on_fusion_path_changed(self.fusion_path_line_edit.text())

    def on_folder_path_changed(self, path: str):
        """Check project folder path and subfolders"""
        storyboard_sub_folder = os.path.join(path, "META\\STORYBOARD")
        if os.path.exists(storyboard_sub_folder):
            self.folder_path_line_edit.setStyleSheet("border-color : rgba(80,100,0, 255)")
            self.start_btn.setEnabled(True)
        else:
            self.folder_path_line_edit.setStyleSheet("border-color : rgba(138,37,30,255);")
            self.start_btn.setEnabled(False)

    def on_fusion_chck_changed(self, state: bool):
        """Enable or disable using Fusion template file"""
        self.fusion_path_line_edit.setEnabled(state)
        self.on_fusion_path_changed(self.fusion_path_line_edit.text())
        self.on_folder_path_changed(self.folder_path_line_edit.text())

    def on_fusion_path_changed(self, path: str):
        """Check Fusion template file"""
        path = path.replace('"', '')
        if os.path.exists(path) and os.path.splitext(path)[1] == '.comp':
            self.fusion_path_line_edit.setStyleSheet("border-color : rgba(80,100,0, 255)")
            self.start_btn.setEnabled(True)
        else:
            self.fusion_path_line_edit.setStyleSheet("border-color : rgba(138,37,30,255);")
            if self.fusion_chck.isChecked():
                self.start_btn.setEnabled(False)

    def on_clickstart_btn(self):
        """Start the folder creation routine"""
        folder_path = self.folder_path_line_edit.text()
        template_path = self.fusion_path_line_edit.text()
        template_path = template_path.replace('"', '')
        self.destroy()
        self.create_fusion_folders(folder_path, template_path, self.fusion_chck.isChecked())

    # #############################################################################
    # Define logic
    # #############################################################################

    def create_fusion_folders(self, folder_path: str, template_path: str, use_template: bool):
        """Execute the folder creation routine"""
        # Gather shots data
        shots = self.get_shots_data(folder_path)
        fusion_folder = os.path.join(folder_path, "FUSION")

        # Create basic folder structure
        if not os.path.exists(fusion_folder):
            os.makedirs(fusion_folder)

        # Create a folder for each shot. Copy the fusion template file inside if possible
        for shot in shots:
            shot_name = shot["Name"]
            shot_folder = os.path.join(fusion_folder, shot_name)
            output_folder = os.path.join(shot_folder, "OUTPUT")

            if not os.path.exists(shot_folder):
                os.makedirs(shot_folder)

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            if template_path and use_template:
                self.copy_fusion_template_file(shot_name, shot_folder, template_path, shot["FrameInterval"], folder_path)

    def get_shots_data(self, folder_path: str):
        """Gather the necessary information about every shot in the current movie"""
        storyboard_file = os.path.join(folder_path, "META\\STORYBOARD", "storyboard.data")
        # Check if the storyboard file exists and open it to load its data
        if not os.path.exists(storyboard_file):
            ms.messagebox("The storyboard data file cannot be found. Make sure the storyboard data is correct before using this script")
            return False
        with open(storyboard_file, 'r') as file:
            json_data = json.load(file)

        # Parse the shots to extract required information (Name and FrameInterval)
        shots = json_data["Shots"]
        shot_info = []
        for shot in shots:
            shot_name = shot["Name"]
            shot_frames = shot["FrameInterval"]
            shot_info.append({"Name": shot_name, "FrameInterval": shot_frames})

        return shot_info

    def copy_fusion_template_file(self, shot_name: str, shot_folder: str, template_path: str, shot_frames: str, root_folder: str):
        """Copy and setup the Fusion template file"""
        comp_file_name = f"{shot_name}.comp"
        comp_file_path = os.path.join(shot_folder, comp_file_name)
        if not os.path.exists(comp_file_path):
            shutil.copy(template_path, comp_file_path)
            shot_frame_range = self.translate_shot_frame_range(shot_frames)

            # Open the Fusion comp file and read it
            with open(comp_file_path, 'r') as file:
                contents = file.read()

            # Setup frame range
            contents = self.fusion_setup_frame_range(contents, shot_frame_range)

            # Setup output saver
            contents = self.fusion_setup_output_saver(contents, shot_folder, shot_name)

            # Find the output folder for this shot
            project_name = os.path.basename(root_folder)
            output_server = extVars.Path.Output.getSociety(root_folder)
            if output_server:
                output_server = extVars.Path.outputServer[output_server]
            render_folder = os.path.join(output_server, project_name, "FILM", shot_name)

            # Setup input saver
            if os.path.exists(render_folder):
                contents = self.fusion_setup_input_loader(contents, render_folder, shot_name)

            # Write the changes back to file
            with open(comp_file_path, 'w') as file:
                file.write(contents)
        else:
            print(f"AutoFusionFolder - {comp_file_name} already exists and has been skipped")

    def translate_shot_frame_range(self, frame_range: str):
        """Translate frame range from storyboard file to Fusion comp format"""
        translation = "{" + frame_range.replace("-", ", ") + "}"
        return translation

    def fusion_setup_frame_range(self, content: str, frame_range: str):
        """Use regular expressions to find and edit comp render range"""
        content = re.sub(r'CurrentTime\s*=\s*\d+', 'CurrentTime = 0', content)
        content = re.sub(r'RenderRange\s*=\s*{[^}]+}', f'RenderRange = {frame_range}', content)
        content = re.sub(r'GlobalRange\s*=\s*{[^}]+}', f'GlobalRange = {frame_range}', content)
        return content

    def fusion_setup_output_saver(self, content: str, shot_folder: str, shot_name: str):
        """Replace the output saver path with the correct folder"""
        output_file = f"{shot_folder}/OUTPUT/{shot_name}_.exr"
        output_file = output_file.replace("\\", "/")
        content = content.replace("<replace_me_with_output>", output_file)
        return content

    def fusion_setup_input_loader(self, content: str, render_folder: str, shot_name: str):
        """Find the most recent render folder, then find the image sequence inside it"""

        # Find the most recent folder with a name that is only a number
        folders = [folder for folder in os.listdir(render_folder) if os.path.isdir(os.path.join(render_folder, folder))]
        folders = [folder for folder in folders if re.match(r"^\d+$", folder)]
        folders = sorted(folders, key=lambda folder: os.path.getmtime(os.path.join(render_folder, folder)), reverse=True)
        if len(folders) > 0:
            most_recent_folder = os.path.join(render_folder, folders[0])
        else:
            print(f"Suitable folder not found for {shot_name}")
            return content

        # Find the first file of an image sequence in the most recent folder
        image_files = [file for file in os.listdir(most_recent_folder) if os.path.isfile(os.path.join(most_recent_folder, file))]
        image_files = [file for file in image_files if re.match(r".*\d+\.\w+$", file)]
        if any("_denoised" in file_name for file_name in image_files):
            image_files = [file for file in image_files if "_denoised" in file]
        image_files = sorted(image_files, key=lambda file: int(re.search(r"\d+", file).group()))
        if len(image_files) > 0:
            first_image_file = os.path.join(most_recent_folder, image_files[0])
            first_image_file = first_image_file.replace("\\", "/")
        else:
            print(f"Suitable image file not found for {shot_name}")
            return content

        content = content.replace("<replace_me_with_input>", first_image_file)
        return content

# ############################################################################
# Execution - Debug ##########################################################
# ############################################################################


if __name__ == "__main__":
    try:
        asyAutoFolder.destroy()
    except:
        pass
    asyAutoFolder = AutoFusionFolder()
