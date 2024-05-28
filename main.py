import csv
import os
import shutil
import sys
import time
import json

import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QKeySequence, QValidator
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QCheckBox, QFileDialog, QDesktopWidget, QLineEdit, \
    QRadioButton, QShortcut, QMessageBox
from xlsxwriter.workbook import Workbook

from ipydex import IPS, activate_ips_on_exception
activate_ips_on_exception()
import confloader


def get_img_paths(dir, extensions=('.jpg', '.png', '.jpeg')):
    '''
    :param dir: folder with files
    :param extensions: tuple with file endings. e.g. ('.jpg', '.png'). Files with these endings will be added to img_paths
    :return: list of all filenames
    '''

    img_paths = []

    for filename in os.listdir(dir):
        if filename.lower().endswith(extensions):
            img_paths.append(os.path.join(dir, filename))

    img_paths.sort()


    if not img_paths:
        msg = f"no image found in {dir}"
        raise FileNotFoundError(msg)
    return img_paths


def make_folder(directory):
    """
    Make folder if it doesn't already exist
    :param directory: The folder destination path
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

# global data storage:
ds = confloader.Container()
ds.path_specified_via_cli = None
ds.last_folder_name = None
STATUS_JSON_NAME = "status.json"


class SetupWindow(QWidget, confloader.Confloader):
    def __init__(self):
        super().__init__()

        self.load_settings_from_toml()

        # Window variables
        self.width = self.conf.get("width", 800)
        self.height = self.conf.get("height", 920)

        # State variables
        self.selected_folder = ''
        self.selected_labels = ''
        self.num_labels = 0

        # these are the input fields
        self.label_inputs = []
        self.label_headlines = []
        self.mode = 'csv'  # default option

        # Labels
        self.username = QLabel('1. Nutzername eingeben', self)
        self.headline_folder = QLabel('2. Ordner auswählen', self)
        # self.headline_num_labels = QLabel('3. Specify labels', self)
        # self.labels_file_description = QLabel(
        #     'a) select file with labels (text file containing one label on each line)', self)
        # self.labels_inputs_description = QLabel('b) or specify how many unique labels you want to assign', self)

        # self.headline_num_labels = QLabel('3. How many unique labels do you want to assign?', self)

        self.selected_folder_label = QLabel(self)
        self.last_folder_label = QLabel(self)
        self.last_user_label = QLabel(self)
        self.last_timestamp_label = QLabel(self)
        self.error_message = QLabel(self)

        # Buttons
        self.browse_button = QtWidgets.QPushButton("Durchsuchen", self)
        # self.confirm_num_labels = QtWidgets.QPushButton("Ok", self)
        self.next_button = QtWidgets.QPushButton("Weiter", self)
        # self.browse_labels_button = QtWidgets.QPushButton("Select labels", self)

        # Inputs
        self.nameInput = QLineEdit(self)
        # self.numLabelsInput = QLineEdit(self)

        # Validation
        # self.onlyInt = QIntValidator()

        self.nameInput.textChanged.connect(self.name_changed)

        #layouts
        # self.formLayout =QFormLayout()

        #GroupBoxs
        # self.groupBox = QGroupBox()

        #Scrolls
        # self.scroll = QScrollArea(self)

        # Init
        self.init_ui()

        # distribute the values from the toml to other variables
        self.load_config()

    def name_changed(self, name):

        # s contains the text of the line edit, we could also test self.lineedit.text()

        if name:
            self.set_next_button_activation(True)
            self.next_button.setStyleSheet(self.button_style_white_bg_blue)
        else:
            self.set_next_button_activation(False)
            self.next_button.setStyleSheet(self.button_style_white_bg_gray)

    def set_next_button_activation(self, active):

        if active:
            self.next_button.setDisabled(False)
        else:
            self.next_button.setDisabled(True)


    def init_ui(self):
        # self.selectFolderDialog = QFileDialog.getExistingDirectory(self, 'Select directory')
        self.set_next_button_activation(False)
        self.setWindowTitle('PyQt5 - Annotation tool - Parameters setup')
        self.setGeometry(0, 0, self.width, self.height)
        self.centerOnScreen()
        sfle = 200 if ds.path_specified_via_cli else 0


        self.button_style = "color: black; font-size: 18pt;"
        self.button_style_white_bg_gray = "color: white; font-size: 18pt; background-color: #999;"
        self.button_style_white_bg_blue = "color: white; font-size: 18pt; background-color: #1E88E5;"

        label_style = 'color: black; font-weight: bold; font-size: 18pt;'

        self.username.setGeometry(60, 30, 400, 35)
        self.username.setStyleSheet(label_style)
        self.nameInput.setGeometry(60, 70, 550 + sfle, 36)
        self.nameInput.setStyleSheet(label_style)

        self.headline_folder.setGeometry(60, 150, 500, 20)
        self.headline_folder.setObjectName("headline")
        self.headline_folder.setStyleSheet(label_style)

        self.selected_folder_label.setGeometry(60, 200, 550 + sfle, 36)
        self.selected_folder_label.setObjectName("selectedFolderLabel")
        self.selected_folder_label.setStyleSheet(label_style)

        self.last_folder_label.setGeometry(60, 300, 550, 36)
        # self.last_folder_label.setStyleSheet(label_style)

        self.last_user_label.setGeometry(60, 350, 550, 36)
        # self.last_user_label.setStyleSheet(label_style)

        self.last_timestamp_label.setGeometry(60, 400, 550, 36)
        # self.last_timestamp_label.setStyleSheet(label_style)

        if ds.last_metadata:
            timestamp = ds.last_metadata.get("timestamp_save")
            self.last_folder_label.setText(f"Zuletzt abgeschlossen: {ds.last_metadata.get('last_completed_folder')}")
            self.last_user_label.setText(f"von: {ds.last_metadata.get('username')}")
            self.last_timestamp_label.setText(f"Zeitstempel: {timestamp}")

        self.browse_button.setGeometry(631, 200, 190, 36)
        self.browse_button.setStyleSheet(label_style)
        self.browse_button.clicked.connect(self.pick_new)
        if ds.path_specified_via_cli:
            self.browse_button.hide()

        # Input number of labels
        top_margin_num_labels = 260
        # self.headline_num_labels.move(60, top_margin_num_labels)
        # self.headline_num_labels.setObjectName("headline")

        # self.labels_file_description.move(60, top_margin_num_labels + 30)
        # self.browse_labels_button.setGeometry(60, top_margin_num_labels + 60, 80, 28)
        # self.browse_labels_button.setGeometry(520, top_margin_num_labels + 25, 89, 28)

        # self.browse_labels_button.clicked.connect(self.pick_labels_file)

        # self.labels_inputs_description.move(60, top_margin_num_labels + 100)
        # self.labels_inputs_description.move(60, top_margin_num_labels + 60)
        # self.numLabelsInput.setGeometry(60, top_margin_num_labels + 130, 60, 26)
        # self.numLabelsInput.setGeometry(75, top_margin_num_labels + 90, 60, 26)
        # self.nameInput.setValidator(self.onlyInt)


        # self.confirm_num_labels.setGeometry(136, top_margin_num_labels + 89, 80, 28)
        # self.confirm_num_labels.clicked.connect(self.generate_label_inputs)

        # Next Button
        # self.next_button.move(360, 630)

        self.next_button.setGeometry(320, 630, 100, 36)
        self.next_button.setStyleSheet(self.button_style_white_bg_gray)
        # self.next_button.setObjectName("blueButton")
        self.next_button.clicked.connect(self.continue_app)

        # Erro message
        self.error_message.setGeometry(20, 810, self.width - 20, 20)
        self.error_message.setAlignment(Qt.AlignCenter)
        self.error_message.setStyleSheet('color: red; font-weight: bold')

        # self.init_radio_buttons()

        #initiate the ScrollArea
        # self.scroll.setGeometry(60, 400, 300, 200)

        # apply custom styles
        try:
            styles_path = "./styles.qss"
            with open(styles_path, "r") as fh:
                self.setStyleSheet(fh.read())
        except:
            print("Can't load custom stylesheet.")

    def load_config(self):
        self.load_settings_from_toml()

        self.selected_folder_label.setText(ds.path)
        self.selected_folder = ds.path

        self.conf_labels = labels = self.conf.label_headlines
        # self.numLabelsInput.setText(str(len(labels)))
        self.generate_label_inputs()

        # fill the input fileds with loaded labels
        for input, label in zip(self.label_inputs, labels):
            input.setText(label)

        self.nameInput.setFocus()
        self.nameInput.keyPressEvent = self.catch_enter(self.nameInput.keyPressEvent, self.activate_next_button)
        self.next_button.keyPressEvent = self.catch_enter(self.next_button.keyPressEvent, self.click_next_button)

    def catch_enter(self, orig_event_handler, on_enter_func):
        def new_event_handler(e):
            orig_event_handler(e)
            if e.key()  in(Qt.Key_Return, Qt.Key_Enter):
                on_enter_func()
        return new_event_handler

    def activate_next_button(self):
        if self.nameInput.text():
            self.next_button.setFocus()
            self.next_button.setStyleSheet(f"{self.button_style_white_bg_blue} border: 1px solid blue;")

    def click_next_button(self):
        self.continue_app()


    def init_radio_buttons(self):
        """
        Creates section with mode selection
        """

        top_margin = 115
        radio_label = QLabel('2. Select mode', self)
        radio_label.setObjectName("headline")
        radio_label.move(60, top_margin)

        radiobutton = QRadioButton(
            "csv (Images in selected folder are labeled and then csv file with assigned labels is generated.)", self)
        radiobutton.setChecked(True)
        radiobutton.mode = "csv"
        radiobutton.toggled.connect(self.mode_changed)
        radiobutton.move(60, top_margin + 35)

        radiobutton = QRadioButton(
            "copy (Creates folder for each label. Labeled images are copied to these folders. Csv is also generated)",
            self)
        radiobutton.mode = "copy"
        radiobutton.toggled.connect(self.mode_changed)
        radiobutton.move(60, top_margin + 65)

        radiobutton = QRadioButton(
            "move (Creates folder for each label. Labeled images are moved to these folders. Csv is also generated)",
            self)
        radiobutton.mode = "move"
        radiobutton.toggled.connect(self.mode_changed)
        radiobutton.move(60, top_margin + 95)

    def mode_changed(self):
        """
        Sets new mode (one of: csv, copy, move)
        """
        radioButton = self.sender()
        if radioButton.isChecked():
            self.mode = radioButton.mode

    def pick_new(self):
        """
        shows a dialog to choose folder with images to label
        """
        dialog = QFileDialog()
        folder_path = dialog.getExistingDirectory(None, "Select Folder")

        self.selected_folder_label.setText(folder_path)
        self.selected_folder = folder_path

    def pick_labels_file(self):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "Select labels", "",
                                                  "Text files (*.txt)", options=options)
        if fileName:
            with open(fileName) as f:
                content = f.readlines()

            labels = [line.rstrip('\n') for line in content]

            self.numLabelsInput.setText(str(len(labels)))
            self.generate_label_inputs()

            # fill the input fileds with loaded labels
            for input, label in zip(self.label_inputs, labels):
                input.setText(label)

    def generate_label_inputs(self):
        """
        Generates input fields for labels. The layout depends on the number of labels.
        """

        # check that number of labels is not empty
        if 1 or self.numLabelsInput.text().strip() != '':

            # convert string (number of labels) to integer
            # self.num_labels = int(self.numLabelsInput.text())
            self.num_labels = len(self.conf_labels)

            # delete previously generated widgets
            for input, headline in zip(self.label_inputs, self.label_headlines):
                input.deleteLater()
                headline.deleteLater()

            # initialize values
            self.label_inputs = []
            self.label_headlines = []  # labels to label input fields
            margin_top = 400

            # show headline for this step
            # self.groupBox.setTitle('4. Fill in the labels and click "Next"')
            # self.groupBox.setStyleSheet('font-weight: bold')

            # diplsay input fields
            for i in range(self.num_labels):
                break
                # append widgets to lists
                self.label_inputs.append(QtWidgets.QLineEdit(self))
                self.label_headlines.append(QLabel(f'label {i + 1}:', self))
                # self.formLayout.addRow(self.label_headlines[i], self.label_inputs[i])

            # self.groupBox.setLayout(self.formLayout)
            # self.scroll.setWidget(self.groupBox)
            # self.scroll.setWidgetResizable(True)
    def centerOnScreen(self):
        """
        Centers the window on the screen.
        """
        resolution = QDesktopWidget().screenGeometry()
        self.move(int((resolution.width() / 2) - (self.width / 2)),
                  int((resolution.height() / 2) - (self.height / 2)) - 40)

    def check_validity(self):
        """
        :return: if all the necessary information is provided for proper run of application. And error message
        """
        if self.selected_folder == '':
            return False, 'Input folder has to be selected (step 1)'

        # num_labels_input = self.numLabelsInput.text().strip()
        # if num_labels_input == '' or num_labels_input == '0':
        #     return False, 'Number of labels has to be number greater than 0 (step 3).'

        return True, "Form Ok."

        if len(self.label_inputs) == 0:
            return False, "You didn't provide any labels. Select number of labels and press \"Ok\""

        for label in self.label_inputs:
            if label.text().strip() == '':
                return False, 'All label fields has to be filled (step 4).'

        return True, 'Form ok'

    def continue_app(self):
        """
        If the setup form is valid, the LabelerWindow is opened and all necessary information is passed to it
        """
        form_is_valid, message = self.check_validity()

        if form_is_valid:
            label_values = self.conf.label_headlines
            # for label in self.label_inputs:
            #     label_values.append(label.text().strip())

            self.close()
            # show window in full-screen mode (window is maximized)
            LabelerWindow(label_values, self.selected_folder, self.nameInput.text()).showMaximized()
        else:
            self.error_message.setText(message)


class LabelerWindow(QWidget):
    def __init__(self, labels, input_folder, username):
        self.username = username
        self.timestamp_start = time.strftime("%Y-%m-%d %H:%M:%S")
        self.last_img_reached = False
        mode = "csv"
        super().__init__()

        # init UI state
        self.title = 'PyQt5 - Annotation tool for assigning image classes'
        self.left = 200
        self.top = 100


        self.button_style = "color: black; font-size: 18pt;"
        # self.button_style_white = "color: white; font-size: 18pt;"

        self.button_style_white_bg_gray = "color: white; font-size: 18pt; background-color: #999;"
        self.button_style_white_bg_blue = "color: white; font-size: 18pt; background-color: #1E88E5;"

        self.label_style_red18 = 'color: red; font-weight: bold; font-size: 18pt;'

        zoom = 1.0

        # Window variables
        self.width = int(50*zoom)
        self.height = int(200*zoom)
        # img panel size should be square-like to prevent some problems with different aspect ratios
        self.img_panel_width = int(650*zoom)  # 650
        self.img_panel_height = int(650*zoom)  # 650

        # state variables
        self.counter = 0
        self.input_folder = input_folder
        self.img_paths = get_img_paths(input_folder)
        self.labels = labels
        self.num_labels = len(self.labels)
        self.num_images = len(self.img_paths)
        self.assigned_labels = {}
        self.mode = mode
        self.btn_label_map = {}

        # initialize list to save all label buttons
        self.label_buttons = []

        # Initialize Labels
        self.image_box = QLabel(self)
        self.last_img_hint = QLabel("", self)
        self.img_name_label = QLabel(self)
        self.progress_bar = QLabel(self)
        self.curr_image_headline = QLabel(f"Nutzer: {self.username}", self)
        self.csv_note = QLabel('Bitte auch Fehler benennen, die leicht auffällig sind, aber nicht\nausgeschleust werden müssten.\n\nWenn keine Auffälligkeit zu sehen ist, dann keine Fehlerklasse markieren.', self)
        self.csv_generated_message = QLabel(self) # will contain "csv saved to ..."
        self.show_next_checkbox = QCheckBox("Automatisch nächstes Bild anzeigen nach dem Annotieren", self)
        # self.generate_xlsx_checkbox = QCheckBox("Also generate .xlsx file", self)

        # create label folders
        if mode == 'copy' or mode == 'move':
            self.create_label_folders(labels, self.input_folder)

        # init UI
        self.init_ui()

    def init_ui(self):

        self.setWindowTitle(self.title)
        # self.setGeometry(self.left, self.top, self.width, self.height) # initial dimension of the window
        self.setMinimumSize(self.width, self.height)  # minimum size of the window

        # create buttons
        self.init_buttons()

        # create 'show next automatically' checkbox
        self.show_next_checkbox.setChecked(False)
        self.show_next_checkbox.setGeometry(self.img_panel_width + 20, 10, 550, 20)

        # "create xlsx" checkbox
        # self.generate_xlsx_checkbox.setChecked(False)
        # self.generate_xlsx_checkbox.setGeometry(self.img_panel_width + 140, 606, 300, 20)

        # image headline
        self.curr_image_headline.setGeometry(20, 10, 300, 20)
        self.curr_image_headline.setObjectName('headline')

        # image name label
        self.img_name_label.setGeometry(20, 40, self.img_panel_width, 20)

        # progress bar (how many images have I labeled so far)
        self.progress_bar.setGeometry(20, 65, self.img_panel_width, 20)

        # csv note
        self.csv_note.setGeometry(self.img_panel_width + 20, 540, 560, 80)

        # message that csv was generated
        self.csv_generated_message.setGeometry(self.img_panel_width + 20, 700, 600, 40)
        self.csv_generated_message.setStyleSheet('color: #43A047')

        # show image
        self.set_image(self.img_paths[0])
        self.image_box.setGeometry(20, 120, self.img_panel_width, self.img_panel_height)
        self.image_box.setAlignment(Qt.AlignTop)

        # image name
        self.img_name_label.setText(self.img_paths[self.counter])

        # progress bar
        self.progress_bar.setText(f'Bild 1 von {self.num_images}')

        # draw line to for better UX
        ui_line = QLabel(self)
        ui_line.setGeometry(20, 98, 1012, 1)
        ui_line.setStyleSheet('background-color: black')

        # apply custom styles
        try:
            styles_path = "./styles.qss"
            with open(styles_path, "r") as fh:
                self.setStyleSheet(fh.read())
        except:
            print("Can't load custom stylesheet.")

    def init_buttons(self):

        # Add "Prev Image" and "Next Image" buttons
        next_prev_top_margin = 50
        prev_im_btn = QtWidgets.QPushButton("←", self)
        prev_im_btn.move(self.img_panel_width + 20, next_prev_top_margin)
        prev_im_btn.clicked.connect(self.show_prev_image)
        prev_im_btn.setStyleSheet(self.button_style)

        next_im_btn = QtWidgets.QPushButton("→", self)
        next_im_btn.move(self.img_panel_width + 140, next_prev_top_margin)
        next_im_btn.clicked.connect(self.show_next_image)
        next_im_btn.setStyleSheet(self.button_style)

        # Add "Prev Image" and "Next Image" keyboard shortcuts
        prev_im_kbs = QShortcut(QKeySequence("left"), self)
        prev_im_kbs.activated.connect(self.show_prev_image)

        next_im_kbs = QShortcut(QKeySequence("right"), self)
        next_im_kbs.activated.connect(self.show_next_image)

        # Add "generate csv file" button
        self.save_res_btn = QtWidgets.QPushButton("CSV speichern", self)
        self.save_res_btn.setGeometry(self.img_panel_width + 20, 750, 500, 50)
        self.save_res_btn.clicked.connect(lambda state, filename='assigned_classes': self.generate_csv(filename))
        self.save_res_btn.setObjectName("blueButton")
        self.save_res_btn.setStyleSheet(self.button_style_white_bg_gray)

        self.last_img_hint.setGeometry(self.img_panel_width + 20, 650, 650, 30)
        self.last_img_hint.setStyleSheet(self.label_style_red18)

        # Create button for each label
        x_shift = 0  # variable that helps to compute x-coordinate of button in UI
        for i, label in enumerate(self.labels):
            j = i + 1

            key = j % 10

            button_text = f"({j}): {label}"

            self.label_buttons.append(QtWidgets.QPushButton(button_text, self))
            button = self.label_buttons[i]

            # this is used to colorize the buttons later:
            self.btn_label_map[label] = button
            button.setStyleSheet(self.button_style)

            # create click event (set label)
            # https://stackoverflow.com/questions/35819538/using-lambda-expression-to-connect-slots-in-pyqt
            button.clicked.connect(lambda state, x=label: self.set_label(x))

            # create keyboard shortcut event (set label)
            # shortcuts start getting overwritten when number of labels >9
            label_kbs = QShortcut(QKeySequence(f"{key}"), self)
            label_kbs.activated.connect(lambda x=label: self.set_label(x))
            print(label_kbs)

            # place button in GUI (create multiple columns if there is more than 10 button)
            y_shift = (30 + 20) * (i % 10)
            if (i != 0 and i % 10 == 0):
                x_shift += 120
                y_shift = 0

            button.move(self.img_panel_width + 20 + x_shift, y_shift + 120)

    def set_label(self, label):
        """
        Sets the label for just loaded image
        :param label: selected label
        """

        print(f"{label=}")

        # get image filename from path (./data/images/img1.jpg → img1.jpg)
        img_path = self.img_paths[self.counter]
        img_name = os.path.split(img_path)[-1]

        # if the img has some label already
        if img_name in self.assigned_labels.keys():

            # label is already there = means tht user want's to remove label
            if label in self.assigned_labels[img_name]:
                self.assigned_labels[img_name].remove(label)

                # remove key from dictionary if no labels are assigned to this image
                if len(self.assigned_labels[img_name]) == 0:
                    self.assigned_labels.pop(img_name, None)

                # remove image from appropriate folder
                if self.mode == 'copy':
                    os.remove(os.path.join(self.input_folder, label, img_name))

                elif self.mode == 'move':
                    # label was in assigned labels, so I want to remove it from label folder,
                    # but this was the last label, so move the image to input folder.
                    # Don't remove it, because it it not save anywehre else
                    if img_name not in self.assigned_labels.keys():
                        shutil.move(os.path.join(self.input_folder, label, img_name), self.input_folder)
                    else:
                        # label was in assigned labels and the image is store in another label folder,
                        # so I want to remove it from current label folder
                        os.remove(os.path.join(self.input_folder, label, img_name))

            # label is not there yet. But the image has some labels already
            else:
                self.assigned_labels[img_name].append(label)

                # path to copy/move images
                copy_to = os.path.join(self.input_folder, label)

                # copy/move the image into appropriate label folder
                if self.mode == 'copy':
                    # the image is stored in input_folder, so i can copy it from there (differs from 'move' option)
                    shutil.copy(img_path, copy_to)

                elif self.mode == 'move':
                    # the image doesn't have to be stored in input_folder anymore.
                    # get the path where the image is stored
                    copy_from = os.path.join(self.input_folder, self.assigned_labels[img_name][0], img_name)
                    shutil.copy(copy_from, copy_to)

        else:
            # Image has no labels yet. Set new label and copy/move

            self.assigned_labels[img_name] = [label]
            # move copy images to appropriate directories
            copy_to = os.path.join(self.input_folder, label)

            if self.mode == 'copy':
                shutil.copy(img_path, copy_to)
            elif self.mode == 'move':
                shutil.move(img_path, copy_to)

        # load next image
        if self.show_next_checkbox.isChecked():
            self.show_next_image()
        else:
            self.set_button_color(img_name)

    def show_next_image(self):
        """
        loads and shows next image in dataset
        """

        if self.counter < self.num_images - 1:
            self.counter += 1

        print(f"{self.counter=}")

        path = self.img_paths[self.counter]
        filename = os.path.split(path)[-1]

        self.set_image(path)
        self.img_name_label.setText(path)
        self.progress_bar.setText(f'Bild {self.counter + 1} von {self.num_images}')
        self.set_button_color(filename)

        if self.counter < self.num_images - 1:
            # not the last image
            self.csv_generated_message.setText('')
            return

        # if this is the last image in dataset
        if self.counter == self.num_images - 1:
            self.last_img_reached = True
            self.last_img_hint.setText("Letztes Bild erreicht. Bitte CSV-Datei speichern.")
            self.save_res_btn.setStyleSheet(self.button_style_white_bg_blue)
            self.save_res_btn.setText("CSV speichern und beenden")

            # change button color (make choice visible)
            path = self.img_paths[self.counter]
            self.set_button_color(os.path.split(path)[-1])

    def show_prev_image(self):
        """
        loads and shows previous image in dataset
        """
        if self.counter > 0:
            self.counter -= 1

            if self.counter < self.num_images:
                self.last_img_hint.setText("")
                path = self.img_paths[self.counter]
                filename = os.path.split(path)[-1]

                # If we have already assigned label to this image and mode is 'move', change the input path.
                # The reason is that the image was moved from '.../input_folder' to '.../input_folder/label'
                if self.mode == 'move' and filename in self.assigned_labels.keys():
                    path = os.path.join(self.input_folder, self.assigned_labels[filename][0], filename)

                self.set_image(path)
                self.img_name_label.setText(path)
                self.progress_bar.setText(f'Bild {self.counter + 1} von {self.num_images}')

                self.set_button_color(filename)
                self.csv_generated_message.setText('')

    def set_image(self, path):
        """
        displays the image in GUI
        :param path: relative path to the image that should be show
        """

        pixmap = QPixmap(path)

        # get original image dimensions
        img_width = pixmap.width()
        img_height = pixmap.height()

        # scale the image properly so it fits into the image window ()
        margin = 20
        if img_width >= img_height:
            pixmap = pixmap.scaledToWidth(self.img_panel_width - margin)

        else:
            pixmap = pixmap.scaledToHeight(self.img_panel_height - margin)

        self.image_box.setPixmap(pixmap)

    def generate_csv(self, out_filename):
        """
        Generates and saves csv file with assigned labels.
        Assigned label is represented as one-hot vector.
        :param out_filename: name of csv file to be generated
        """
        path_to_save = os.path.join(self.input_folder, 'output')
        make_folder(path_to_save)
        csv_file_path = os.path.join(path_to_save, out_filename) + '.csv'

        with open(csv_file_path, "w", newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')

            # write header
            writer.writerow(['img'] + self.labels)

            # write one-hot labels
            for img_name, labels in self.assigned_labels.items():
                labels_one_hot = self.labels_to_zero_one(labels)
                writer.writerow([img_name] + list(labels_one_hot))

        metadata_path = os.path.join(path_to_save, "metadata.json")

        metadata = {
            "last_completed_folder": self.input_folder,
            "username": self.username,
            "timestamp_start": self.timestamp_start,
            "timestamp_save": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(metadata_path, "w", encoding='utf-8') as fp:
            json.dump(metadata, fp, ensure_ascii=False, indent=4)

        message = f'CSV-Datei erfolgreich gespeichert:\n{csv_file_path}'
        self.csv_generated_message.setText(message)
        print(message)

        # also save the metadata in parent folder to easily display it on setup window
        self.save_metadata_to_parent_folder(metadata)
        if self.last_img_reached:
            self.close()

        if 0 and self.generate_xlsx_checkbox.isChecked():
            try:
                self.csv_to_xlsx(csv_file_path)
            except:
                print('Generating xlsx file failed.')

    def save_metadata_to_parent_folder(self, metadata):
        assert isinstance(metadata, dict)
        parent = os.path.dirname(os.path.abspath(self.input_folder))
        json_path = os.path.join(parent, STATUS_JSON_NAME)

        dirname = os.path.split(os.path.abspath(self.input_folder))[-1]
        try:
            with open(json_path, "w") as fp:
                json.dump(metadata, fp)
        except Exception as ex:
            print(ex)
            raise



    def csv_to_xlsx(self, csv_file_path):
        """
        converts csv file to xlsx file
        :param csv_file_path: path to csv file which we want to convert to lsx
        """
        workbook = Workbook(csv_file_path[:-4] + '.xlsx')
        worksheet = workbook.add_worksheet()

        with open(csv_file_path, 'rt', encoding='utf8') as f:
            reader = csv.reader(f)
            for r, row in enumerate(reader):
                for c, col in enumerate(row):
                    worksheet.write(r, c, col)

        workbook.close()

    def set_button_color(self, filename):
        """
        changes color of button which corresponds to selected label
        :filename filename of loaded image:
        """

        if filename in self.assigned_labels.keys():
            assigned_labels = self.assigned_labels[filename]
        else:
            assigned_labels = []

        for label, button in self.btn_label_map.items():

            if label in assigned_labels:
                button.setStyleSheet(self.button_style + ' border: 1px solid #43A047; background-color: #4CAF50; color: white')
            else:
                button.setStyleSheet(self.button_style + ' background-color: None')

    def closeEvent(self, event):
        """
        This function is executed when the app is closed.
        It automatically generates csv file in case the user forgot to do that
        """
        print("closing the App..")
        self.generate_csv('assigned_classes_automatically_generated')

    def labels_to_zero_one(self, labels):
        """
        Convert number to one-hot vector
        :param number: number which represents for example class index
        :param num_classes: number of classes in dataset so I know how long the vector should be
        :return:
        """

        # create mapping from label name to its index for better efficiency {label : int}
        label_to_int = dict((c, i) for i, c in enumerate(self.labels))

        # initialize array to save selected labels
        zero_one_arr = np.zeros([self.num_labels], dtype=int)
        for label in labels:
            zero_one_arr[label_to_int[label]] = 1

        return zero_one_arr

    @staticmethod
    def create_label_folders(labels, folder):
        for label in labels:
            make_folder(os.path.join(folder, label))

def handle_cli_data_folder(sys_argv: list):
    """
    process sys.argv and set relevant variables of global data storage ds.
    """

    ds.cli_errors = []
    fallback = True

    cl = confloader.Confloader()
    cl.load_settings_from_toml()


    if "--data" in sys_argv:
        idx1 = sys_argv.index("--data")
        sys_argv.pop(idx1)
        ds.path_specified_via_cli = None
        try:
            ds.path = sys_argv.pop(idx1)
        except IndexError:
            ds.cli_errors.append("Could not detect path argument after option `--data`")
            ds.path = None
        if ds.path and os.path.isdir(ds.path):
            fallback = False
            ds.path_specified_via_cli = True
        else:
            ds.cli_errors.append(f"Could not find path: {ds.path}")
    if fallback:
        ds.path = cl.conf.selected_folder

def show_errors(errors: list):

    app = QApplication([])
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    errmsg = '\n'.join(errors)
    msg.setText(f"The following errors occurred: \n\n{errmsg}")
    msg.setWindowTitle("Error")
    sys.exit(msg.exec_())


def get_metadata() -> dict:
    """
    look in parent folder for `status.json`
    """

    parent = os.path.dirname(os.path.abspath(ds.path))
    json_path = os.path.join(parent, STATUS_JSON_NAME)

    try:
        with open(json_path) as fp:
            metadata_dict = json.load(fp)
    except Exception as ex:
        print(ex)
        return None

    return metadata_dict



if __name__ == '__main__':
    # run the application
    handle_cli_data_folder(sys.argv)
    if ds.cli_errors:
        show_errors(ds.cli_errors)

    ds.last_metadata = get_metadata()
    # metadata_dict["last_completed_folder"]
    app = QApplication(sys.argv)
    ex = SetupWindow()
    ex.show()
    sys.exit(app.exec_())
