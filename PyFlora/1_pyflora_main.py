from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QSize, QTimer, QResource
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QWidget, QTabWidget, QDialog, QComboBox, QLabel, QLineEdit, QTextEdit, QStackedLayout, QPushButton, QToolButton, QMenu, QScrollArea, QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt5.QtGui import QPixmap, QFont, QIcon
from sqlalchemy.orm import Session
from sqlalchemy import func
from pyflora_db import db_engine, Users, Plants, Pots, SensorReadings
from bs4 import BeautifulSoup
import resource_rc
from sensor_light import measure_light_intensity
from openweather_temp import current_temperature_ow
from sensor_moisture import initial_soil_moisture, measure_soil_moisture
from sensor_ph import measure_soil_ph
import datetime as dt
import pyqtgraph as pg
from pyqtgraph import plot
import random
import sys


NOTIFICATION_STYLE = """
    QLabel {
        background-color: #A3BAB4;
        border-radius: 10px;
        font: 13pt "Candara";
        padding: 20px
    }
"""
INFO_CLOSE_BUTTON_STYLE = '''
    QPushButton {
        font: bold 12pt "Candara";
        background-color: #A3BAB4;
        border-radius: 10px;
    }

    QPushButton:hover {
        background-color: #92a7a2;
    }

    QPushButton:pressed {
        background-color: #A3BAB4;
        border: 5px solid #92a7a2
    }
'''

PLANTS_LABEL_STYLE = """
    QMenu {
        font-family: Candara;
        font-size: 11pt;
        background-color: #E9E5E3;

    }

    QMenu::item:selected {
        background-color: #D1CECC;

    }

    QMenu::item:pressed {
        background-color: #BAB7B5;
    }
"""
MANAGE_BUTTONS_STYLE = """
    QPushButton {
        background-color: #E9E5E3;
        border-radius: 15px;
    }

    QPushButton:hover{
        background-color: #D1CECC;
    }

    QPushButton:pressed{
        background-color: #E9E5E3;
        border: 4px solid #D1CECC;
    }
"""

EDITABLE_QLINEEDIT_STYLE = """
    QLineEdit {
            background-color: #E2E9E7;
            font: italic 12pt "Candara";
            padding-left: 10px
    }

    QLineEdit:focus {
            border: none;
            outline: none;

    }
"""
NON_EDITABLE_QLINEEDIT_STYLE = """
    QLineEdit {
            background-color: #CFDBD8;
            font: 12pt "Candara";
            padding-left: 10px
    }
"""


class NotificationWindow(QDialog):
    def __init__(self, text):
        super().__init__(flags=Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)

        self.layout = QVBoxLayout()
        self.label = QLabel(text)
        self.label.setStyleSheet(NOTIFICATION_STYLE)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedWidth(302)
        self.label.setWordWrap(True)

        self.layout.addWidget(self.label)
        self.setLayout(self.layout)


class NotificationTime(NotificationWindow):
    def __init__(self, text, duration):
        super().__init__(text)

        self.text = text

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.close)

        self.duration = duration

    def showEvent(self, event):
        super().showEvent(event)

        self.timer.start(self.duration)


class NotificationInfo(NotificationWindow):
    def __init__(self, text):
        super().__init__(text)

        self.text = text

        font = QFont()
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignLeft)

        self.close_button = QPushButton()
        self.close_button.setIcon(QIcon("./close.png"))
        self.close_button.setStyleSheet(INFO_CLOSE_BUTTON_STYLE)
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.close)

        self.layout.insertWidget(0, self.close_button, alignment=Qt.AlignTop | Qt.AlignRight)
        self.layout.setSpacing(0)


class NotificationMessage(NotificationWindow):
    def __init__(self, text):
        super().__init__(text)

        self.text = text
        self.setStyleSheet("background-color: #EFEFEF;")

        self.yes_button = QPushButton("Yes")
        self.yes_button.setStyleSheet(INFO_CLOSE_BUTTON_STYLE)
        self.yes_button.setFixedSize(100, 30)
        self.yes_button.clicked.connect(self.on_yes_button_clicked)

        self.no_button = QPushButton("No")
        self.no_button.setStyleSheet(INFO_CLOSE_BUTTON_STYLE)
        self.no_button.setFixedSize(100, 30)
        self.no_button.clicked.connect(self.on_no_button_clicked)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.yes_button)
        button_layout.addWidget(self.no_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def on_yes_button_clicked(self):
        self.accept()

    def on_no_button_clicked(self):
        self.reject()


class EditButtons(QPushButton):
    def __init__(self, icon_path):
        super().__init__()

        self.setMinimumSize(45, 45)
        self.setIconSize(QSize(25, 25))
        self.setStyleSheet(MANAGE_BUTTONS_STYLE)
        self.setIcon(QIcon(icon_path))


class LoginScreen(QMainWindow):
    def __init__(self):
        super(LoginScreen, self).__init__()

        self.setWindowFlag(Qt.FramelessWindowHint) 

        loadUi("pyflora_login.ui", self)

        self.login_button.clicked.connect(self.authenticate)

        self.setWindowTitle("PyFlora")


    def authenticate(self):

        username = self.username_input.text()
        password = self.password_input.text()

        with Session(bind=db_engine) as session:
            user = session.query(Users).filter(Users.username == username, Users.password == password).one_or_none()

            if user:
                self.close()
                self.home_screen = HomeScreen(user, self)
                self.home_screen.show()
            else:
                self.login_info.setText('Incorrect username or password')

    
    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Escape:
            self.close()
            print("PyFlora app is closed.")


class HomeScreen(QMainWindow):
    def __init__(self, user, login_screen):
        super(HomeScreen, self).__init__()

        self.setWindowFlag(Qt.FramelessWindowHint) 

        loadUi("pyflora_app.ui", self)

        QResource.registerResource('./pyflora.qrc')

        self.setWindowTitle("PyFlora")

        self.user = user
        self.user_id = user.id

        self.pyflora_tabs.setCurrentIndex(0)

        self.login_screen = login_screen

        self.plants_tab = PlantsTab(self)
        self.pots_tab = PotsTab(self)
        self.notification_tab = NotificationTab(self)
        self.home_tab = self.findChild(QWidget, "home_tab")

        self.image_label = self.findChild(QLabel, "image_label")
        self.image_label.setStyleSheet(f"border-image: url({user.image_path}); \
                            background-position: center; \
                            background-repeat: no-repeat; \
                            background-clip: border-box; \
                            background-color: transparent; \
                            border-radius: 40px;")


        self.greeting_label = self.findChild(QLabel, "greeting_label")

        welcome_messages = [
            "Let's get gardening!",
            "Let's dive into plant care!",
            "Step into the world of plant nurturing!",
            "Let's nourish and flourish together!",
            "Ready to care for your leafy companions?",
            "Unleash your inner plant whisperer!"
        ]

        random_message = random.choice(welcome_messages)

        self.greeting_label.setText(f"<span style='font-weight: bold; font-size: 14pt;'>Hello, {user.first_name}!</span><br> {random_message}")

        self.profile_button.clicked.connect(lambda: self.profile_clicked(user))
        self.plants_button.clicked.connect(lambda: self.pyflora_tabs.setCurrentIndex(1))
        self.pots_button.clicked.connect(lambda: self.pyflora_tabs.setCurrentIndex(2))
        self.settings_button.clicked.connect(self.home_info_message)
        self.logout_button.clicked.connect(self.logout)

        self.pyflora_tabs.currentChanged.connect(self.reset_and_clear)

        self.home_info = self.pyflora_tabs.findChild(QLabel, "home_info")
        self.home_layout = self.pyflora_tabs.findChild(QVBoxLayout, "home_layout")
        self.home_all = self.pyflora_tabs.findChild(QWidget, "home_all")

        self.stacklayout_home = QStackedLayout()
        self.profile_info = loadUi("profile_info.ui")

        self.stacklayout_home.addWidget(self.home_all)
        self.stacklayout_home.addWidget(self.profile_info)

        layout = self.home_layout
        layout.addLayout(self.stacklayout_home)

        self.verticalLayout_profile = self.profile_info.findChild(QVBoxLayout, "verticalLayout_profile")

        self.return_profile = self.profile_info.findChild(QToolButton, "return_profile")
        self.return_profile.clicked.connect(self.return_home_btn)

        self.manage_profile = self.profile_info.findChild(QToolButton, "manage_profile")
        self.menu_profile = QMenu(self)
        self.edit_profile = self.menu_profile.addAction("Edit profile")
        self.delete_profile = self.menu_profile.addAction("Delete profile")
        self.manage_profile.setMenu(self.menu_profile)
        self.manage_profile.setPopupMode(QToolButton.InstantPopup)
        self.menu_profile.setStyleSheet(PLANTS_LABEL_STYLE)

        self.edit_profile.triggered.connect(self.edit_profile_triggered)
        self.delete_profile.triggered.connect(self.delete_profile_triggered)

        self.profile_edit_widgets_created = False


    def logout(self):
    
        self.close()
        self.login_screen = LoginScreen()
        self.login_screen.show()


    def home_info_message(self):

        self.home_info.setText("Settings page is under maintenance!")


    def reset_and_clear(self, index):

        if index == 0:
            self.stacklayout_home.setCurrentIndex(0)
        elif index == 1:
            self.plants_tab.stacklayout.setCurrentIndex(0)
        elif index == 2:
            self.pots_tab.stacklayout_pots.setCurrentIndex(0)

        for widget in self.findChildren((QLineEdit, QTextEdit)):
            if widget.isEnabled():
                widget.clear()

        self.home_info.clear()
        

    def populate_profile_info(self, user):

        self.profile_photo = self.profile_info.findChild(QLabel, "profile_photo")
        self.experience_garden = self.profile_info.findChild(QLabel, "experience_garden")
        self.gardener_name = self.profile_info.findChild(QLineEdit, "gardener_name")
        self.number_plants = self.profile_info.findChild(QLabel, "number_plants")
        self.number_pots = self.profile_info.findChild(QLabel, "number_pots")

        if user:

            self.profile_photo.setStyleSheet(f"border-image: url({user.image_path}); \
                            background-position: center; \
                            background-repeat: no-repeat; \
                            background-clip: border-box; \
                            background-color: transparent; \
                            border-radius: 40px;")

            self.gardener_name.setText(f"{user.first_name} {user.last_name}")

            with Session(bind=db_engine) as session:
                plant_count = session.query(func.count(Plants.id)).scalar()
                pot_count = session.query(func.count(Pots.id)).scalar()

            self.number_plants.setText(str(plant_count))
            self.number_pots.setText(str(pot_count))


            if pot_count <= 3:
                self.experience_garden.setText(f"<span style='font-weight: bold; font-size: 13pt;'>Blossom Beginner</span><br><br>\
                                               The first step to becoming a great gardener is embracing the joy of getting your hands dirty.")
            elif 3 < pot_count < 7:
                self.experience_garden.setText(f"<span style='font-weight: bold; font-size: 13pt;'>Sprout Specialist</span><br><br>\
                                               Your journey through plant care has cultivated not just beautiful gardens, but a wealth of knowledge.")
            else:
                self.experience_garden.setText(f"<span style='font-weight: bold; font-size: 13pt;'>Garden Guru</span><br><br>\
                                               Plant care is not just about the greenery; it's about cultivating a deeper connection with nature.")


    def profile_clicked (self, user):

            self.stacklayout_home.setCurrentIndex(1)
            self.populate_profile_info(user)


    def return_home_btn(self):

        self.stacklayout_home.setCurrentIndex(0)

        self.profile_set_default()
        self.reset_and_clear(0)


    def edit_profile_triggered(self, user):

        if hasattr(self, 'profile_info_label1') and self.profile_info_label1.text():
            self.profile_info_label1.clear()
        
        if not self.profile_edit_widgets_created:
            self.create_profile_edit_widgets()
            self.profile_edit_widgets_created = True


    def delete_profile_triggered(self):

        self.credentials_layout1 = QVBoxLayout()
        self.credentials_layout1.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_profile.addLayout(self.credentials_layout1)

        self.profile_info_label1 = QLabel()
        self.profile_info_label1.setStyleSheet("font: 12pt Candara; padding: 7px; color: #BD523F; qproperty-alignment: AlignCenter;")
        self.credentials_layout1.addWidget(self.profile_info_label1)

        self.profile_info_label1.setText("Delete profile option is under maintenance!")


    def create_profile_edit_widgets(self):

        self.credentials_layout = QVBoxLayout()
        self.credentials_layout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_profile.addLayout(self.credentials_layout)

        self.username_edit = QLineEdit()
        self.username_edit.setFixedHeight(40)
        self.username_edit.setStyleSheet(EDITABLE_QLINEEDIT_STYLE)
        self.username_edit.setPlaceholderText("Type your new username here")
        self.credentials_layout.addWidget(self.username_edit)

        self.credentials_layout.addSpacing(6)

        self.password_edit = QLineEdit()
        self.password_edit.setFixedHeight(40)
        self.password_edit.setStyleSheet(EDITABLE_QLINEEDIT_STYLE)
        self.password_edit.setPlaceholderText("Type your new password here")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.credentials_layout.addWidget(self.password_edit)

        self.credentials_layout.addSpacing(6)

        self.password_check = QLineEdit()
        self.password_check.setFixedHeight(40)
        self.password_check.setStyleSheet(EDITABLE_QLINEEDIT_STYLE)
        self.password_check.setPlaceholderText("Re-type your new password here")
        self.password_check.setEchoMode(QLineEdit.Password)
        self.credentials_layout.addWidget(self.password_check)

        self.profile_info_label = QLabel()
        self.profile_info_label.setStyleSheet("font: 13pt Candara; padding: 7px; color: #BD523F; qproperty-alignment: AlignCenter;")
        self.credentials_layout.addWidget(self.profile_info_label)

        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 20, 0, 0)
        self.verticalLayout_profile.addLayout(self.button_layout)
        self.button_layout.setAlignment(Qt.AlignHCenter)

        self.discard_button = EditButtons("./close.png")
        self.button_layout.addWidget(self.discard_button)
        self.discard_button.clicked.connect(self.discard_changes_profile)

        self.button_layout.addSpacing(6)

        self.save_button = EditButtons("./check.png")
        self.button_layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save_changes_profile)

        self.gardener_name.setReadOnly(False)
        self.gardener_name.setStyleSheet(EDITABLE_QLINEEDIT_STYLE)


    def save_changes_profile(self, user_id):

        user_id = self.user_id
        print(user_id)

        edited_full_name = self.gardener_name.text()
        edited_first_name, edited_last_name = edited_full_name.split()

        with Session(bind=db_engine) as local_session:
            user = local_session.query(Users).filter(Users.id == user_id).one_or_none()

            if user:

                password = self.password_edit.text()
                password_check = self.password_check.text()

                if password == password_check and password != "":

                    user.first_name = edited_first_name
                    user.last_name = edited_last_name
                    user.username = self.username_edit.text()
                    user.password = password


                    self.notification10 = NotificationTime(f"You have successfully updated your profile!", 3000)
                    self.notification10.show()

                    self.stacklayout_home.setCurrentIndex(0)
                    self.profile_set_default()

                else:
                    self.profile_info_label.setText("Password Mismatch. Please try again.")

                local_session.commit()


    def discard_changes_profile(self):

        self.profile_set_default()


    def profile_set_default(self):

        if hasattr(self, 'credentials_layout'):

            while self.credentials_layout.count():
                item = self.credentials_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        if hasattr(self, 'button_layout'):

            while self.button_layout.count():
                item = self.button_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        if hasattr(self, 'credentials_layout1'):

            while self.credentials_layout1.count():
                item = self.credentials_layout1.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        self.gardener_name.setReadOnly(True)
        self.gardener_name.setStyleSheet(NON_EDITABLE_QLINEEDIT_STYLE)

        self.profile_edit_widgets_created = False


class PlantsTab(QLabel):
    def __init__(self, home_screen):
        super(PlantsTab, self).__init__()

        self.home_screen = home_screen
        #self.plants_tab = plants_tab
        self.user_id = self.home_screen.user_id

        self.file_name = None

        self.pyflora_tabs = self.home_screen.findChild(QTabWidget, "pyflora_tabs")
        self.plants_tab = self.pyflora_tabs.findChild(QWidget, "plants_tab")
        self.centralwidget = self.home_screen.findChild(QWidget, "centralwidget")
        self.plants_all = self.home_screen.findChild(QWidget, "plants_all")
        self.plants_layout = self.home_screen.findChild(QVBoxLayout, "plants_layout")

        self.search_plants = self.home_screen.findChild(QLineEdit, "search_plants")
        self.search_plants.setFocusPolicy(Qt.WheelFocus)
        self.search_plants.setFocus(True)

        self.stacklayout = QStackedLayout()
        self.plants_info = loadUi("plants_info.ui")
        self.plants_add = loadUi("plants_add.ui")

        self.stacklayout.addWidget(self.plants_all)
        self.stacklayout.addWidget(self.plants_info)
        self.stacklayout.addWidget(self.plants_add)

        layout = self.plants_layout
        layout.addLayout(self.stacklayout)

        self.scroll_plants = self.home_screen.findChild(QScrollArea, "scroll_plants")
        self.plants_widget = self.home_screen.findChild(QWidget, "plants_widget")

        with Session(bind=db_engine) as session:
            plants = session.query(Plants).all()

        for plant in plants:
            self.plant_label = QLabel()
            self.plant_label.setMinimumSize(260,80)
            self.plant_label.setProperty("id", str(plant.id))
            self.plant_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.plant_label.setText(f"<span style='font-weight: bold; font-size: 13pt;'>{plant.name}</span><br>{plant.botanical_name}")

            if plant.image_loc is not None:

                self.plant_label.setStyleSheet(f"background-image: url({plant.image_loc}); background-position: center; background-repeat: no-repeat;\
                                    opacity: 1.0; font-family: Candara; font-size: 12pt; color: white; padding-left: 7px; border-radius: 10px;\
                                    ")
            
            else: 
                self.plant_label.setStyleSheet(f"background-color: #E9E5E3; font-family: Candara; font-size: 12pt; color: black;\
                                                padding-left: 7px; border-radius: 10px;")


            self.plants_widget.layout().addWidget(self.plant_label)

            self.plant_label.mousePressEvent = lambda event, plant_label=self.plant_label: self.plant_label_clicked(event, plant_label)

        self.scroll_plants.setWidget(self.plants_widget)
        self.plants_widget.layout().setAlignment(QtCore.Qt.AlignTop)

        self.search_plants.textChanged.connect(lambda text: self.filter_plants(text, self.plants_widget))

        self.add_plant_button = self.home_screen.findChild(QPushButton, "add_plant_button")
        self.add_plant_button.clicked.connect(self.add_plant)

        self.return_plants = self.plants_info.findChild(QToolButton, "return_plants")
        self.return_plants.clicked.connect(self.return_plants_btn)

        self.manage_plant = self.plants_info.findChild(QToolButton, "manage_plant")
        self.menu_plant = QMenu(self)
        self.edit_plant = self.menu_plant.addAction("Edit plant")
        self.delete_plant = self.menu_plant.addAction("Delete plant")
        self.manage_plant.setMenu(self.menu_plant)
        self.manage_plant.setPopupMode(QToolButton.InstantPopup)
        self.menu_plant.setStyleSheet(PLANTS_LABEL_STYLE)

        self.edit_plant.triggered.connect(self.edit_plant_triggered)
        self.delete_plant.triggered.connect(self.delete_plant_triggered)

        self.form = self.plants_info.findChild(QWidget, "Form")
        self.verticalLayout_2 = self.plants_info.findChild(QVBoxLayout, "verticalLayout_2")
        self.verticalLayout = self.plants_info.findChild(QVBoxLayout, "verticalLayout")

        self.plant_edit_widgets_created = False


    def repopulate_plants(self):

        with Session(bind=db_engine) as session:
            plants = session.query(Plants).all()

        while self.plants_widget.layout().count():
            item = self.plants_widget.layout().takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for plant in plants:
            self.plant_label = QLabel()
            self.plant_label.setMinimumSize(260,80)
            self.plant_label.setProperty("id", str(plant.id))
            self.plant_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.plant_label.setText(f"<span style='font-weight: bold; font-size: 13pt;'>{plant.name}</span><br>{plant.botanical_name}")

            if plant.image_loc is not None:
                
                self.plant_label.setStyleSheet(f"background-image: url({plant.image_loc}); background-position: center; background-repeat: no-repeat;\
                                    opacity: 1.0; font-family: Candara; font-size: 12pt; color: white; padding-left: 7px; border-radius: 10px;\
                                    ")
                
            else: 
                self.plant_label.setStyleSheet(f"background-color: #E9E5E3; font-family: Candara; font-size: 12pt; color: black;\
                                                padding-left: 7px; border-radius: 10px;")

            self.plants_widget.layout().addWidget(self.plant_label)

            self.plant_label.mousePressEvent = lambda event, plant_label=self.plant_label: self.plant_label_clicked(event, plant_label)


    def add_plant(self):

        self.stacklayout.setCurrentIndex(2)

        self.plant_image_add = self.plants_add.findChild(QLabel, "plant_image_add")
        self.upload_plant_image_add = self.plants_add.findChild(QPushButton, "upload_plant_image_add")
        self.plant_name_add = self.plants_add.findChild(QTextEdit, "plant_name_add")
        self.botanical_name_add = self.plants_add.findChild(QTextEdit, "botanical_name_add")
        self.watering_info_add = self.plants_add.findChild(QLineEdit, "watering_info_add")
        self.sunlight_info_add = self.plants_add.findChild(QLineEdit, "sunlight_info_add")
        self.substrate_info_add = self.plants_add.findChild(QLineEdit, "substrate_info_add")
        self.ph_info_add = self.plants_add.findChild(QLineEdit, "ph_info_add")
        self.info_add = self.plants_add.findChild(QLabel, "info_add")
        self.save_button_add = self.plants_add.findChild(QPushButton, "save_button_add")
        self.discard_button_add = self.plants_add.findChild(QPushButton, "discard_button_add")

        self.upload_plant_image_add.clicked.connect(self.upload_plant_image)
        self.save_button_add.clicked.connect(lambda: self.save_new_plant(self.user_id))
        self.discard_button_add.clicked.connect(self.discard_new_plant)


    def upload_plant_image(self):

        self.file_name,_ = QFileDialog.getOpenFileName(self, 'Open Image', '', 'Image files (*.jpg *.png)')

        if self.file_name:

            self.plant_image_add.setStyleSheet(f"border-image: url({self.file_name}) 0 0 0 0 stretch stretch; \
                            background-position: center; \
                            background-repeat: no-repeat; \
                            background-clip: border-box; \
                            background-color: transparent; \
                            border-radius: 40px;")


    def save_new_plant(self, user_id):

        self.user_id = self.home_screen.user_id

        with Session(bind=db_engine) as local_session:
            existing_plant = local_session.query(Plants).filter_by(name=self.plant_name_add.toPlainText()).one_or_none()

            if existing_plant:
                self.info_add.setText(f"<b>{existing_plant.name}</b> plant is already in your database!")

            else:
                new_plant = Plants(
                    user_id = self.user_id,
                    name = self.plant_name_add.toPlainText(),
                    botanical_name = self.botanical_name_add.toPlainText(),
                    watering = self.watering_info_add.text(),
                    sun_exposure = self.sunlight_info_add.text(),
                    substrate = self.substrate_info_add.text(),
                    soil_ph = self.ph_info_add.text()
                )

                if self.file_name:
                    new_plant.image_loc = self.file_name

                local_session.add(new_plant)
                local_session.commit()

                self.repopulate_plants()

                self.stacklayout.setCurrentIndex(0)
                self.notification1 = NotificationTime(f"You have successfully added <b>{new_plant.name}</b> plant to your database!", 3000)
                self.notification1.show()

                self.home_screen.reset_and_clear(1)


    def discard_new_plant(self):

        self.home_screen.reset_and_clear(1)


    def edit_plant_triggered(self):

        plant_id = self.current_plant_id
        print(plant_id)

        if not self.plant_edit_widgets_created:
            self.create_plant_edit_widgets()
            self.plant_edit_widgets_created = True


    def create_plant_edit_widgets(self):

        self.button_layout = QHBoxLayout()
        self.verticalLayout.addLayout(self.button_layout)
        self.button_layout.setAlignment(Qt.AlignHCenter)

        self.discard_button = EditButtons("./close.png")
        self.button_layout.addWidget(self.discard_button)
        self.discard_button.clicked.connect(self.discard_changes_plants)

        self.save_button = EditButtons("./check.png")
        self.button_layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save_changes_plants)

        self.plant_name.setReadOnly(False)
        self.plant_name.setStyleSheet("background-color: #E2E9E7")

        self.watering_info.setReadOnly(False)
        self.watering_info.setStyleSheet(EDITABLE_QLINEEDIT_STYLE)

        self.sunlight_info.setReadOnly(False)
        self.sunlight_info.setStyleSheet(EDITABLE_QLINEEDIT_STYLE)

        self.substrate_info.setReadOnly(False)
        self.substrate_info.setStyleSheet(EDITABLE_QLINEEDIT_STYLE)

        self.ph_info.setReadOnly(False)
        self.ph_info.setStyleSheet(EDITABLE_QLINEEDIT_STYLE)


    def default_plant_info(self):
        #after saving or discarding changes, plant_info is set back to default

        self.plant_name.setReadOnly(True)
        self.plant_name.setStyleSheet("")

        self.watering_info.setReadOnly(True)
        self.watering_info.setStyleSheet(NON_EDITABLE_QLINEEDIT_STYLE)

        self.sunlight_info.setReadOnly(True)
        self.sunlight_info.setStyleSheet(NON_EDITABLE_QLINEEDIT_STYLE)

        self.substrate_info.setReadOnly(True)
        self.substrate_info.setStyleSheet(NON_EDITABLE_QLINEEDIT_STYLE)

        self.ph_info.setReadOnly(True)
        self.ph_info.setStyleSheet(NON_EDITABLE_QLINEEDIT_STYLE)

        if hasattr(self, 'button_layout'):

            while self.button_layout.count():
                item = self.button_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        self.plant_edit_widgets_created = False


    def discard_changes_plants(self):

        plant_id = self.current_plant_id

        with Session(bind=db_engine) as session:
            plant = session.query(Plants).filter(Plants.id == plant_id).one_or_none()

            print(plant_id)
            self.watering_info.setText(f"{plant.watering}")
            self.sunlight_info.setText(f"{plant.sun_exposure}")
            self.substrate_info.setText(f"{plant.substrate}")
            session.commit()

        self.default_plant_info()


    def save_changes_plants(self, plant_id):

        plant_id = self.current_plant_id

        html_content = self.plant_name.toHtml()
        soup = BeautifulSoup(html_content, 'html.parser')

        name_span = soup.select_one('p span:nth-of-type(1)')
        botanical_span = soup.select_one('p span:nth-of-type(2)')

        self.plant_name_extracted = name_span.get_text(strip=True) if name_span else ''
        self.botanical_name_extracted = botanical_span.get_text(strip=True) if name_span else ''

        with Session(bind=db_engine) as local_session:
            plant = local_session.query(Plants).filter(Plants.id == plant_id).one_or_none()

            print(plant_id)
            plant.name = self.plant_name_extracted
            plant.botanical_name = self.botanical_name_extracted

            plant.watering = self.watering_info.text()
            plant.sun_exposure = self.sunlight_info.text()
            plant.substrate = self.substrate_info.text()
            local_session.commit()

        self.default_plant_info()
        self.repopulate_plants()


    def return_plants_btn(self):

        self.stacklayout.setCurrentIndex(0)

        self.default_plant_info()


    def delete_plant_triggered(self, plant_id):

        plant_id = self.current_plant_id

        with Session(bind=db_engine) as session:
            plant = session.query(Plants).filter(Plants.id == plant_id).one_or_none()

        confirmation1 = NotificationMessage(f"Are you sure you want to delete <b>{plant.name}</b> plant?")

        if confirmation1.exec_() == QDialog.Accepted:

            with Session(bind=db_engine) as session:
                plant = session.query(Plants).filter(Plants.id == plant_id).one_or_none()

            if plant:

                for child in self.plants_widget.children():
                    if isinstance(child, QLabel) and child.property("id") == plant_id:
                        plant_label = child
                        break

                if plant_label:

                    self.stacklayout.setCurrentIndex(0)
                    self.plants_widget.layout().removeWidget(plant_label)
                    plant_label.setParent(None)
                    plant_label.deleteLater()
                    self.plants_widget.layout().update()

                session.delete(plant)
                session.commit()

                self.notification2 = NotificationTime(f"You have successfully deleted <b>{plant.name}</b> plant from your database!", 3000)
                self.notification2.show()


    def filter_plants(self, text, plants_widget):
        for i in range(plants_widget.layout().count()):
            widget = plants_widget.layout().itemAt(i).widget()
            plants_widget.layout().setAlignment(QtCore.Qt.AlignTop)
            label_text = widget.text().lower()
            search_text = text.lower()

            br_index = label_text.find("</span><br>")
            plant_name = label_text[50:br_index]
            botanical_name = label_text[br_index + len("</span><br>"):]

            if len(search_text) == 1:

                if plant_name.startswith(text.lower()) or botanical_name.startswith(text.lower()):
                    widget.show()

                else:
                    widget.hide()

            elif len(search_text) > 1:
                if search_text in plant_name or search_text in botanical_name:
                    widget.show()
                else:
                    widget.hide()

            else:
                widget.show()


    def plant_label_clicked(self, event, plant_label):

        if event.button() == Qt.LeftButton:

            plant_id = plant_label.property("id")
            self.current_plant_id = plant_label.property("id")
            print(plant_id)
            self.stacklayout.setCurrentIndex(1)
            self.populate_plants_info(plant_id)


    def populate_plants_info(self, plant_id):

        self.plant_name = self.plants_info.findChild(QTextEdit, "plant_name")
        self.plant_image = self.plants_info.findChild(QLabel, "plant_image")
        self.watering_info = self.plants_info.findChild(QLineEdit, "watering_info")
        self.sunlight_info = self.plants_info.findChild(QLineEdit, "sunlight_info")
        self.substrate_info = self.plants_info.findChild(QLineEdit, "substrate_info")
        self.ph_info = self.plants_info.findChild(QLineEdit, "ph_info")

        with Session(bind=db_engine) as session:
            plant = session.query(Plants).filter(Plants.id == plant_id).one_or_none()
            print(plant_id)

            self.plant_name.setHtml(f"<span style='font-weight: bold; font-size: 13pt;'>{plant.name}</span><br><span style='font-size: 10pt;'>{plant.botanical_name}")
            self.plant_name.setReadOnly(True)

            if plant.image_loc is not None:

                self.plant_image.setStyleSheet(f"border-image: url({plant.image_loc}) 0 0 0 0 stretch stretch; \
                                background-position: center; \
                                background-repeat: no-repeat; \
                                background-clip: border-box; \
                                background-color: transparent; \
                                border-radius: 40px;")
                
            self.watering_info.setText(f"{plant.watering}")
            self.watering_info.setReadOnly(True)
            self.sunlight_info.setText(f"{plant.sun_exposure}")
            self.sunlight_info.setReadOnly(True)
            self.substrate_info.setText(f"{plant.substrate}")
            self.substrate_info.setReadOnly(True)
            self.ph_info.setText(f"{plant.soil_ph}")
            self.ph_info.setReadOnly(True)


class PotsTab(QWidget):
    def __init__(self, home_screen):
        super(PotsTab, self).__init__()

        self.home_screen = home_screen
        #self.plants_tab = plants_tab
        self.user_id = self.home_screen.user_id

        #self.file_name = None

        self.is_edit_mode = False

        self.pyflora_tabs = self.home_screen.findChild(QTabWidget, "pyflora_tabs")
        self.pots_tab = self.pyflora_tabs.findChild(QWidget, "pots_tab")
        self.centralwidget = self.home_screen.findChild(QWidget, "centralwidget")
        self.pots_all = self.home_screen.findChild(QWidget, "pots_all")
        self.pots_layout = self.home_screen.findChild(QVBoxLayout, "pots_layout")

        self.search_pots = self.home_screen.findChild(QLineEdit, "search_pots")
        self.search_pots.setFocusPolicy(Qt.WheelFocus)
        self.search_pots.setFocus(True)

        self.stacklayout_pots = QStackedLayout()
        self.pots_info = loadUi("pots_info.ui")
        self.pots_add = loadUi("pots_add.ui")
        self.populate_combo_boxes()

        self.stacklayout_pots.addWidget(self.pots_all)
        self.stacklayout_pots.addWidget(self.pots_info)
        self.stacklayout_pots.addWidget(self.pots_add)

        layout = self.pots_layout
        layout.addLayout(self.stacklayout_pots)

        self.scroll_pots = self.home_screen.findChild(QScrollArea, "scroll_pots")
        self.pots_widget = self.home_screen.findChild(QWidget, "pots_widget")

        with Session(bind=db_engine) as session:
            pots = session.query(Pots).all()
            
        for pot in pots:
            self.pot_widget = QWidget()
            self.pot_layout = QHBoxLayout(self.pot_widget)
            self.pot_layout.setContentsMargins(0, 0, 0, 0)
            self.pot_layout.setSpacing(0)
            self.pot_image_label = QLabel()
            self.pot_image_label.setFixedSize(80,80)
            #self.pot_image_label.setProperty("id", str(pot.id))
            self.pot_info_label = QLabel()
            self.pot_info_label.setObjectName("pot_info_label")
            #self.pot_info_label.setProperty("id", str(pot.id))
            self.pot_widget.layout().addWidget(self.pot_image_label)
            self.pot_widget.layout().addWidget(self.pot_info_label)
            self.pot_widget.setMinimumSize(260,80)
            self.pot_widget.setProperty("id", str(pot.id))
            self.pot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.pot_widget.setStyleSheet("background-color: #CFDBD8; border-radius: 30px;")
            self.pot_info_label.setText(f"<span style='font-weight: bold; font-size: 13pt;'>{pot.name}</span><br>{pot.plant_name}")

            if pot.plant_image is not None:

                self.pot_image_label.setStyleSheet(f"border-image: url({pot.plant_image}); background-position: center; background-repeat: no-repeat;\
                                    opacity: 1.0; border-radius: 30px")
                
            self.pot_info_label.setStyleSheet("font-family: Candara; font-size: 12pt; padding-left: 7px; border-radius: 30px;")
            

            self.pots_widget.layout().addWidget(self.pot_widget)

            self.pot_widget.mousePressEvent = lambda event, pot_widget=self.pot_widget: self.pot_widget_clicked(event, pot_widget)

        self.scroll_pots.setWidget(self.pots_widget)
        self.pots_widget.layout().setAlignment(QtCore.Qt.AlignTop)

        #print(self.pot_info_label.text())

        self.search_pots.textChanged.connect(lambda text: self.filter_pots(text, self.pots_widget))

        self.sync_button = self.home_screen.findChild(QPushButton, "sync_button")
        self.sync_button.clicked.connect(self.sync_all_pots)

        self.add_pot_button = self.home_screen.findChild(QPushButton, "add_pot_button")
        self.add_pot_button.clicked.connect(self.add_pot)

        self.return_pots = self.pots_info.findChild(QToolButton, "return_pots")
        self.return_pots.clicked.connect(lambda: self.stacklayout_pots.setCurrentIndex(0))
        self.return_pots.clicked.connect(self.destroy_graph)

        self.sync_pot = self.pots_info.findChild(QPushButton, "sync_pot")
        self.sync_pot.clicked.connect(self.fetch_sensor_reading_pot)

        self.water_pot = self.pots_info.findChild(QPushButton, "water_pot")
        self.water_pot.clicked.connect(self.watering_pot)

        self.sensor_graphs = self.pots_info.findChild(QWidget, "sensor_graphs")

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#E9E5E3')
        self.graph_widget_layout = QVBoxLayout()
        self.graph_widget_layout.setContentsMargins(0, 0, 0, 0)
        self.graph_widget_layout.addWidget(self.plot_widget)
        self.sensor_graphs.setLayout(self.graph_widget_layout)

        self.manage_pot = self.pots_info.findChild(QToolButton, "manage_pot")
        self.menu_pot = QMenu(self)
        self.pot_setup = self.menu_pot.addAction("Pot setup")
        self.edit_pot = self.menu_pot.addAction("Edit pot")
        self.delete_pot = self.menu_pot.addAction("Delete pot")
        self.manage_pot.setMenu(self.menu_pot)
        self.manage_pot.setPopupMode(QToolButton.InstantPopup)
        self.menu_pot.setStyleSheet(PLANTS_LABEL_STYLE)

        self.delete_pot.triggered.connect(self.delete_pot_triggered)
        self.edit_pot.triggered.connect(self.edit_pot_triggered)
        self.pot_setup.triggered.connect(self.pot_setup_text)

        self.form = self.pots_info.findChild(QWidget, "Form")
        self.verticalLayout = self.pots_info.findChild(QVBoxLayout, "verticalLayout")
        self.horizontalLayout = self.pots_info.findChild(QHBoxLayout, "horizontalLayout")
        self.verticalLayout_2 = self.pots_info.findChild(QVBoxLayout, "verticalLayout_2")
        self.verticalLayout_3 = self.pots_info.findChild(QVBoxLayout, "verticalLayout_3")
        self.verticalLayout_4 = self.pots_info.findChild(QVBoxLayout, "verticalLayout_4")

        self.pots_info_btn.clicked.connect(self.info_pots_parameters)
        self.save_add_pot.clicked.connect(self.save_button_clicked)

        self.discard_add_pot.clicked.connect(self.discard_new_pot)


    def save_button_clicked(self):

        if self.is_edit_mode:
            self.save_changes_pots(self.current_pot_id)

            self.is_edit_mode = False
        else:
            self.save_new_pot(self.user_id)


    def repopulate_pots(self):

        with Session(bind=db_engine) as session:
            pots = session.query(Pots).all()

        while self.pots_widget.layout().count():
            item = self.pots_widget.layout().takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for pot in pots:
            self.pot_widget = QWidget()
            self.pot_layout = QHBoxLayout(self.pot_widget)
            self.pot_layout.setContentsMargins(0, 0, 0, 0)
            self.pot_layout.setSpacing(0)
            self.pot_image_label = QLabel()
            self.pot_image_label.setFixedSize(80,80)
            #self.pot_image_label.setProperty("id", str(pot.id))
            self.pot_info_label = QLabel()
            self.pot_info_label.setObjectName("pot_info_label")
            #self.pot_info_label.setProperty("id", str(pot.id))
            self.pot_widget.layout().addWidget(self.pot_image_label)
            self.pot_widget.layout().addWidget(self.pot_info_label)
            self.pot_widget.setMinimumSize(260,80)
            self.pot_widget.setProperty("id", str(pot.id))
            self.pot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.pot_widget.setStyleSheet("background-color: #CFDBD8; border-radius: 30px;")
            self.pot_info_label.setText(f"<span style='font-weight: bold; font-size: 13pt;'>{pot.name}</span><br>{pot.plant_name}<br>")
            self.pot_info_label.setStyleSheet("font-family: Candara; font-size: 12pt; padding-left: 7px; border-radius: 30px;")

            if pot.plant_image is not None:

                self.pot_image_label.setStyleSheet(f"border-image: url({pot.plant_image}); background-position: center; background-repeat: no-repeat;\
                                    opacity: 1.0; border-radius: 30px")
    
            self.pots_widget.layout().addWidget(self.pot_widget)

            self.pot_widget.mousePressEvent = lambda event, pot_widget=self.pot_widget: self.pot_widget_clicked(event, pot_widget)


    def populate_combo_boxes(self, plant=None, location=None, light_intensity=None, moisture=None):

        self.plant_options = self.pots_add.findChild(QComboBox, "plant_options")
        self.location_options = self.pots_add.findChild(QComboBox, "location_options")
        self.light_options = self.pots_add.findChild(QComboBox, "light_options")
        self.moisture_options = self.pots_add.findChild(QComboBox, "moisture_options")
        self.pots_info_btn = self.pots_add.findChild(QPushButton, "pots_info_btn")
        self.info_add_pot = self.pots_add.findChild(QLabel, "info_add_pot")
        self.save_add_pot = self.pots_add.findChild(QPushButton, "save_add_pot")
        self.discard_add_pot = self.pots_add.findChild(QPushButton, "discard_add_pot")

        with Session(bind=db_engine) as local_session:
            plants = local_session.query(Plants).all()

            for plant_obj in plants:
                self.plant_options.addItem(plant_obj.name)

            if plant:
                self.plant_options.setCurrentText(plant)

        locations = ["Living room", "Bathroom", "Bedroom", "Kitchen", "Hall", "Balcony", "Home office", "Garden", "Dining room", "Terrace"]
        sorted_locations = sorted(locations)
        self.location_options.addItems(sorted_locations)

        self.light_options.addItems(["Shade", "Indirect sunlight", "Strong light", "Full sun"])
        self.moisture_options.addItems(["Dry", "Normal", "Wet"])

        self.plant_options.setCurrentText(plant) if plant else self.plant_options.setCurrentIndex(-1)
        self.location_options.setCurrentText(location) if location else self.location_options.setCurrentIndex(-1)
        self.light_options.setCurrentText(light_intensity) if light_intensity else self.light_options.setCurrentIndex(-1)
        self.moisture_options.setCurrentText(moisture) if moisture else self.moisture_options.setCurrentIndex(-1)


    def add_pot(self):

        self.stacklayout_pots.setCurrentIndex(2)

        self.plant_options.setCurrentIndex(-1)
        self.location_options.setCurrentIndex(-1)
        self.light_options.setCurrentIndex(-1)
        self.moisture_options.setCurrentIndex(-1)


    def edit_pot_triggered(self):

        pot_id = self.current_pot_id
        print(pot_id)

        with Session(bind=db_engine) as local_session:
            pot = local_session.query(Pots).filter(Pots.id == pot_id).one_or_none()

        if pot:
            self.stacklayout_pots.setCurrentIndex(2)
            self.plant_options.setCurrentText(pot.plant_name) if pot.plant_name else self.plant_options.setCurrentIndex(-1)
            self.location_options.setCurrentText(pot.location) if pot.location else self.location_options.setCurrentIndex(-1)
            self.light_options.setCurrentText(pot.light_intensity) if pot.light_intensity else self.light_options.setCurrentIndex(-1)
            self.moisture_options.setCurrentText(pot.soil_moisture) if pot.soil_moisture else self.moisture_options.setCurrentIndex(-1)

            self.is_edit_mode = True

        else:
            print("Pot not found!")


    def save_changes_pots(self, pot_id):

        pot_id = self.current_pot_id

        with Session(db_engine) as local_session:
            edited_plant = local_session.query(Plants).filter_by(name=self.plant_options.currentText()).one_or_none()

            if edited_plant:
                pot_id = self.current_pot_id
                pot = local_session.query(Pots).filter_by(id=pot_id).one_or_none()

                if pot:
                    pot.name = f"Pot {pot_id} - {self.location_options.currentText()}"
                    pot.plant_id = edited_plant.id
                    pot.plant_name = edited_plant.name
                    pot.plant_image = edited_plant.image_loc
                    pot.location = self.location_options.currentText()
                    pot.light_intensity = self.light_options.currentText()
                    pot.soil_moisture = self.moisture_options.currentText()

                    soil_moisture = self.moisture_options.currentText()

                    if soil_moisture == "Wet":
                        soil_moisture_range = '8.0 - 10.0'
                    elif soil_moisture == "Normal":
                        soil_moisture_range = '4.0 - 7.0'
                    elif soil_moisture == "Dry":
                        soil_moisture_range = '1.0 - 3.0'
                    else:
                        soil_moisture_range = ''

                    pot.soil_moisture_range = soil_moisture_range
                    pot.watering = edited_plant.watering
                    pot.soil_ph = edited_plant.soil_ph

                    local_session.commit()

                    self.repopulate_pots()
                    self.populate_pots_info(pot_id)

                    self.stacklayout_pots.setCurrentIndex(1)
                    self.notification8 = NotificationTime(f"You have successfully edited <b>{pot.name}</b>!", 3000)
                    self.notification8.show()

                else:
                    print("Pot not found!")
            else:
                print("Edited plant not found!")


    def save_new_pot(self, user_id):

        with Session(db_engine) as local_session:
            selected_plant = local_session.query(Plants).filter_by(name=self.plant_options.currentText()).one_or_none()

            max_pot_number = local_session.query(func.max(Pots.id)).scalar()
            pot_number = max_pot_number + 1 if max_pot_number else 1

            soil_moisture = self.moisture_options.currentText()

            if soil_moisture == "Wet":
                soil_moisture_range = '8.0 - 10.0'
            elif soil_moisture == "Normal":
                soil_moisture_range = '4.0 - 7.0'
            elif soil_moisture == "Dry":
                soil_moisture_range = '1.0 - 3.0'
            else:
                soil_moisture_range = ''

            location = self.location_options.currentText()
            location = location if location else None
            light_intensity = self.light_options.currentText()
            light_intensity = light_intensity if light_intensity else None
            soil_moisture = self.moisture_options.currentText()
            soil_moisture = soil_moisture if soil_moisture else None

            pot_image = ("./plant_pot.png")

            if selected_plant:
                pot_name = f"Pot {pot_number} - {self.location_options.currentText()}"

                if not location or not light_intensity or not soil_moisture:
                    pot_name = f"Broken pot - {location}" if location else f"Broken pot"
            else:
                pot_name = f"Empty pot - {location}" if location else f"Empty pot"

            new_pot = Pots(
                user_id = user_id,
                plant_id = selected_plant.id if selected_plant else None,
                name = pot_name,
                plant_name = selected_plant.name if selected_plant else None,
                plant_image = selected_plant.image_loc if selected_plant else pot_image,
                location = location,
                light_intensity = light_intensity,
                soil_moisture = soil_moisture,
                soil_moisture_range = soil_moisture_range,
                watering = selected_plant.watering if selected_plant else None,
                soil_ph = selected_plant.soil_ph if selected_plant else None,
            )

            local_session.add(new_pot)
            local_session.commit()

            self.repopulate_pots()

            self.stacklayout_pots.setCurrentIndex(0)
            self.notification3 = NotificationTime(f"You have successfully added <b>{new_pot.name}</b> to your database!", 3000)
            self.notification3.show()


    def discard_new_pot(self):

        self.plant_options.setCurrentIndex(-1)
        self.location_options.setCurrentIndex(-1)
        self.light_options.setCurrentIndex(-1)
        self.moisture_options.setCurrentIndex(-1)

        self.stacklayout_pots.setCurrentIndex(0)


    def filter_pots(self, text, pots_widget):

        for i in range(self.pots_widget.layout().count()):
            widget = pots_widget.layout().itemAt(i).widget()
            pot_info_label = widget.findChild(QLabel, "pot_info_label")
            pots_widget.layout().setAlignment(QtCore.Qt.AlignTop)
            label_text = pot_info_label.text().lower()
            search_text = text.lower()

            br_index = label_text.find("</span><br>")
            pot_name = label_text[50:br_index]
            plant_name = label_text[br_index + len("</span><br>"):]

            print(pot_name, plant_name)

            if len(search_text) == 1:

                if pot_name.startswith(text.lower()) or plant_name.startswith(text.lower()):
                    widget.show()

                else:
                    widget.hide()

            elif len(search_text) > 1:
                if search_text in pot_name.lower() or search_text in plant_name.lower():
                    widget.show()
                else:
                    widget.hide()

            else:
                widget.show()


    def pot_widget_clicked(self, event, pot_widget):

        if event.button() == Qt.LeftButton:

            pot_id = pot_widget.property("id")
            self.current_pot_id = pot_widget.property("id")
            #self.current_pot_id = self.pot_widget.property("id")
            #self.current_pot_id = self.pot_info_label.property("id")
            #self.current_pot_id = self.pot_image_label.property("id")

            print(pot_id)
            self.stacklayout_pots.setCurrentIndex(1)
            self.populate_pots_info(pot_id)
            self.watering_record(pot_id)


    def populate_pots_info(self, pot_id):

        self.pot_name = self.pots_info.findChild(QLabel, "pot_name")
        self.pot_plant = self.pots_info.findChild(QLabel, "pot_plant")
        self.pot_watering = self.pots_info.findChild(QLabel, "pot_watering")
        self.last_watered = self.pots_info.findChild(QLabel, "last_watered")
        self.moisture_range = self.pots_info.findChild(QLabel, "moisture_range")
        self.sensor_graphs = self.pots_info.findChild(QWidget, "sensor_graphs")

        with Session(bind=db_engine) as session:
            pot = session.query(Pots).filter(Pots.id == pot_id).one_or_none()
            print(pot_id)

            self.pot_name.setText(f"{pot.name}")
            self.pot_plant.setText(f"{pot.plant_name}")
            self.pot_watering.setText(f"{pot.watering}")
            self.moisture_range.setText(f"{pot.soil_moisture_range}")

        self.sync_pot.setProperty("id", str(pot.id))
        self.sensor_graph(pot_id)


    def fetch_sensor_reading_pot(self, pot_id):

        pot_id = self.current_pot_id

        #pot_id = self.sync_pot.property("id")
        print(pot_id)

        current_time = dt.datetime.now()

        with Session(bind=db_engine) as local_session:
            pot = local_session.query(Pots).filter(Pots.id == pot_id).one_or_none()

            if pot:

                pot_name = pot.name

                if 'empty' in pot_name.lower() or 'broken' in pot_name.lower():

                    print("Pot is empty or broken. No reading.")
                    self.notification7 = NotificationTime(f"The pot <b>{pot_name}</b> is empty or broken. Sensor is not providing any readings!", 3000)
                    self.notification7.show()

                else:

                    light_intensity = measure_light_intensity(pot.light_intensity)
                    moisture_option = pot.soil_moisture

                    last_reading = local_session.query(SensorReadings).filter(SensorReadings.pot_id == pot.id).order_by(SensorReadings.datetime.desc()).first()

                    if last_reading:
                        moisture_option = moisture_option
                        current_temperature = current_temperature_ow()
                        current_light_intensity = light_intensity
                        last_entry_time = last_reading.datetime
                        time_difference = current_time - last_entry_time
                        time_delta = time_difference.total_seconds()/3600
                        soil_moisture_calc = measure_soil_moisture(moisture_option, current_temperature, current_light_intensity, time_delta)
                        #print(last_entry_time, last_reading, current_time, time_difference, time_delta)

                    else:

                        soil_moisture_calc = initial_soil_moisture(moisture_option)

                    soil_ph_range = pot.soil_ph
                    soil_ph_reading = measure_soil_ph(soil_ph_range)

                    new_reading = SensorReadings(
                        pot_id = pot.id,
                        datetime = current_time,
                        temperature_celsius = current_temperature_ow(),
                        light_intensity_lux = light_intensity,
                        soil_moisture = soil_moisture_calc,
                        soil_ph = soil_ph_reading
                    )

                    local_session.add(new_reading)
                    local_session.commit()

                    self.notification11 = NotificationTime(f"Sensor readings for <b>{pot.name}</b> have been successfully synchronized!", 3000)
                    self.notification11.show()

                    print("Success!")

            else:
                print("Unsuccessful!")

        self.sensor_graph(pot_id)


    def destroy_graph(self):

        self.stacklayout_pots.setCurrentIndex(0)


    def sensor_graph(self, pot_id):

        pot_id = self.sync_pot.property("id")
        print(pot_id)

        self.plot_widget.clear()

        p = self.plot_widget.plotItem

        self.plot_widget.getPlotItem().setContentsMargins(0, 10, 0, 10)

        p.clear()
        p.clearPlots()
        p.vb.clear()

        v2 = pg.ViewBox()

        v2.clear()
        p.scene().addItem(v2)

        p.setTitle("Sensor readings")

        p.getAxis('left').linkToView(p.vb)
        p.getAxis('right').linkToView(v2)
        x_axis = pg.DateAxisItem(orientation='bottom')
        p.setAxisItems({'bottom': x_axis})

        v2.setXLink(p)

        with Session(bind=db_engine) as local_session:
            readings = local_session.query(SensorReadings).filter(SensorReadings.pot_id == pot_id).all()
            #for reading in readings:
                #print(f"Reading - Timestamp: {reading.datetime}, Temperature: {reading.temperature_celsius}, Light Intensity: {reading.light_intensity_lux}, Soil Moisture: {reading.soil_moisture}, Soil pH: {reading.soil_ph}")

        x_data = [reading.datetime.timestamp() for reading in readings]
        y1_data = [reading.temperature_celsius for reading in readings]
        y2_data = [reading.light_intensity_lux for reading in readings]
        y3_data = [reading.soil_moisture for reading in readings]
        y4_data = [reading.soil_ph for reading in readings]

        p.clear()
        p.clearPlots()
        p.vb.clear()
        v2.clear()

        pen1 = pg.mkPen(color='#E07D54', width=2)
        pen2 = pg.mkPen(color='#DB9600', width=2)
        pen3 = pg.mkPen(color='#5E9299', width=2)
        pen4 = pg.mkPen(color='#523D35', width=2)

        curve1 = pg.PlotCurveItem(x_data, y1_data, pen=pen1, name='Temperature')
        curve2 = pg.PlotCurveItem(x_data, y2_data, pen=pen2, name='Light Intensity')
        curve3 = pg.PlotCurveItem(x_data, y3_data, pen=pen3, name='Soil Moisture')
        curve4 = pg.PlotCurveItem(x_data, y4_data, pen=pen4, name='Soil pH')

        p.addItem(curve1)
        p.addItem(curve3)
        p.addItem(curve4)
        #v2.addItem(curve2)

        self.plot_widget.setLabel('left', '<span style="color:#523D35">Soil pH,</span> <span style="color:#5E9299">Soil Moisture,</span> <span style="color:#E07D54">Temperature(°C)</span> ')
        self.plot_widget.setLabel('right', '<span style="color:#DB9600">Light Intensity (LUX)</span>')
        self.plot_widget.setLabel('bottom', 'Time')

        v2.setGeometry(p.vb.sceneBoundingRect())

        v2.linkedViewChanged(p.vb, v2.XAxis)

        p.vb.sigResized.connect(lambda: v2.setGeometry(p.vb.sceneBoundingRect()))

        self.plot_widget.update()


    def sync_all_pots(self):

        current_time = dt.datetime.now()

        with Session(bind=db_engine) as local_session:
            pots = local_session.query(Pots).all()

            for pot in pots:

                pot_id = pot.id
                print(pot_id)
                pot_name = pot.name

                if 'empty' in pot_name.lower() or 'broken' in pot_name.lower():

                    print("Pot is empty or broken. No reading.")

                else:

                    light_intensity = measure_light_intensity(pot.light_intensity)
                    moisture_option = pot.soil_moisture

                    last_reading = local_session.query(SensorReadings).filter(SensorReadings.pot_id == pot.id).order_by(SensorReadings.datetime.desc()).first()

                    if last_reading:
                        moisture_option = moisture_option
                        current_temperature = current_temperature_ow()
                        current_light_intensity = light_intensity
                        last_entry_time = last_reading.datetime
                        time_difference = current_time - last_entry_time
                        time_delta = time_difference.total_seconds()/3600
                        soil_moisture_calc = measure_soil_moisture(moisture_option, current_temperature, current_light_intensity, time_delta)

                    else:

                        soil_moisture_calc = initial_soil_moisture(moisture_option)

                    soil_ph_range = pot.soil_ph
                    soil_ph_reading = measure_soil_ph(soil_ph_range)

                    new_reading = SensorReadings(
                        pot_id = pot.id,
                        datetime = current_time,
                        temperature_celsius = current_temperature_ow(),
                        light_intensity_lux = light_intensity,
                        soil_moisture = soil_moisture_calc,
                        soil_ph = soil_ph_reading
                    )

                    local_session.add(new_reading)
                    local_session.commit()

                    print("Success!")

        self.sensor_graph(pot_id)

        self.notification9 = NotificationTime(f"Sensor readings for all pots have been successfully synchronized!", 3000)
        self.notification9.show()


    def watering_pot(self, pot_id):

        pot_id = self.sync_pot.property("id")
        print(pot_id)

        current_time = dt.datetime.now()

        with Session(bind=db_engine) as local_session:
            pot = local_session.query(Pots).filter(Pots.id == pot_id).one_or_none()

            if pot:

                plant_name = pot.plant_name
                pot_name = pot.name

                if 'empty' in pot_name.lower() or 'broken' in pot_name.lower():

                    print("Pot is empty or broken. No reading.")
                    self.notification5 = NotificationTime(f"The pot <b>{pot_name}</b> is empty or broken. Watering is unavailable!", 3000)
                    self.notification5.show()

                else:

                    last_soil_moisture_reading = (local_session.query(SensorReadings.soil_moisture).filter_by(pot_id=pot.id).order_by(SensorReadings.id.desc()).first())

                    if last_soil_moisture_reading:

                        light_intensity = measure_light_intensity(pot.light_intensity)

                        last_soil_moisture_reading = (local_session.query(SensorReadings.soil_moisture).filter_by(pot_id=pot.id).order_by(SensorReadings.id.desc()).first())
                        last_soil_moisture = last_soil_moisture_reading.soil_moisture
                        print(last_soil_moisture)
                        new_soil_moisture = last_soil_moisture + 1.0

                        new_soil_moisture = max(1, min(10, new_soil_moisture))

                        formatted_soil_moisture = "{:.2f}".format(round(new_soil_moisture, 2))

                        soil_ph_range = pot.soil_ph
                        soil_ph_reading = measure_soil_ph(soil_ph_range)

                        new_reading = SensorReadings(
                            pot_id = pot.id,
                            datetime = current_time,
                            watering_timestamp = current_time,
                            temperature_celsius = current_temperature_ow(),
                            light_intensity_lux = light_intensity,
                            soil_moisture = new_soil_moisture,
                            soil_ph = soil_ph_reading
                        )

                        local_session.add(new_reading)
                        local_session.commit()

                        print("Success!")

                        self.notification6 = NotificationTime(f"You have successfully watered <b>{plant_name}</b> in <b>{pot_name}</b>! The soil moisture level has increased by <b>1</b> point\
                                                            and is now <b>{formatted_soil_moisture}</b>. Make sure to check the moisture range to ensure your plant is well-watered.", 7000)
                        self.notification6.show()

                        self.sensor_graph(pot_id)
                        self.watering_record(pot_id)

                    else:
                        print("Pot doesn't have previous reading.")
                        self.notification5 = NotificationTime(f"Please fetch sensor readings for <b>{pot_name}</b> before watering <b>{plant_name}</b>.", 3000)
                        self.notification5.show()

            else:
                print("Unsuccessful!")


    def pot_setup_text(self, pot_id):

        pot_id = self.current_pot_id

        with Session(bind=db_engine) as local_session:
            pot = local_session.query(Pots).filter(Pots.id == pot_id).one_or_none()

            if pot:
                text = f"""
                <html>
                <body>
                    <h4>Pot setup:</h4>
                    <p>
                        <b>Plant Name:</b> {pot.plant_name}<br>
                        <b>Pot Location:</b> {pot.location}<br>
                        <b>Light Intensity:</b> {pot.light_intensity}<br>
                        <b>Soil Moisture Setup:</b> {pot.soil_moisture}<br>
                        <b>Optimal Moisture Range:</b> {pot.soil_moisture_range}<br>
                        <b>Watering Schedule:</b> {pot.watering}<br>
                        <b>Soil pH Range:</b> {pot.soil_ph}<br>
                    </p>
                </body>
                </html>
                """

            self.pot_setup = NotificationInfo(text)
            self.pot_setup.show()


    def info_pots_parameters(self):

        text = """
            <h4>Light intensity:</h4>
            <p><b>Shade</b> - Suitable for plants placed in rooms without access to natural light or in areas with low light intensity.</p>
            <p><b>Bright indirect sunlight</b> - Ideal for plants positioned in shaded areas that never receive direct sunlight.</p>
            <p><b>Strong light</b> - Recommended for plants that thrive in consistent and strong light intensity.</p>
            <p><b>Full sun</b> - Suitable for plants situated outdoors or near windows, receiving direct sunlight or very bright indoor light.</p>

            <h4>Soil moisture:</h4>
            <p><b>Dry</b> - Plants in this category require watering approximately every couple of weeks and prefer ample sunlight.</p>
            <p><b>Normal</b> - Plants in this category need watering on a weekly basis or at most every 10 days.</p>
            <p><b>Wet</b> - Plants in this category require watering every couple of days.</p>
            """

        self.info_pots = NotificationInfo(text)
        self.info_pots.show()


    def delete_pot_triggered(self, pot_id):

        pot_id = self.current_pot_id

        with Session(bind=db_engine) as session:
            pot = session.query(Pots).filter(Pots.id == pot_id).one_or_none()

        confirmation2 = NotificationMessage(f"Are you sure you want to delete <b>{pot.name}</b>?")

        if confirmation2.exec_() == QDialog.Accepted:
            with Session(bind=db_engine) as session:
                pot = session.query(Pots).filter(Pots.id == pot_id).one_or_none()

            if pot:

                with Session(bind=db_engine) as session:
                    session.query(SensorReadings).filter(SensorReadings.pot_id == pot_id).delete()
                    session.commit()

                for child in self.pots_widget.children():
                    if isinstance(child, QWidget) and child.property("id") == pot_id:
                        pot_widget = child
                        break

                if pot_widget:

                    self.stacklayout_pots.setCurrentIndex(0)
                    self.pots_widget.layout().removeWidget(pot_widget)
                    pot_widget.setParent(None)
                    pot_widget.deleteLater()
                    self.pots_widget.layout().update()

                session.delete(pot)
                session.commit()

                self.notification4 = NotificationTime(f"You have successfully deleted <b>{pot.name}</b> and all its sensor readings from your database!", 3000)
                self.notification4.show()


    def watering_record(self, pot_id):

        pot_id = self.current_pot_id
        current_time = dt.datetime.now()

        with Session(bind=db_engine) as local_session:
            pot = local_session.query(Pots).filter(Pots.id == pot_id).one_or_none()

            if pot:

                last_watering_reading = (local_session.query(SensorReadings).filter(SensorReadings.pot_id == pot_id).order_by(SensorReadings.watering_timestamp.desc()).first())

                if last_watering_reading is not None:

                    last_watering_timestamp = last_watering_reading.watering_timestamp

                    if last_watering_timestamp is not None:

                        days_since_watering = (current_time - last_watering_timestamp).days

                        print(f"Days since last watering: {days_since_watering}")

                        if days_since_watering == 0:
                            self.last_watered.setText("today")

                        elif days_since_watering == 1:
                            self.last_watered.setText("yesterday")

                        else:
                            self.last_watered.setText(f"{days_since_watering} days ago")

                    else:
                        print("No watering records found for the pot")
                        self.last_watered.setText("no previous watering")

                else:
                    self.last_watered.setText("no previous watering")

            else:
                print("Pot not found in the database")

   
class NotificationTab(QWidget):
    def __init__(self, home_screen):
        super(NotificationTab, self).__init__()

        self.home_screen = home_screen
        self.user_id = self.home_screen.user_id

        self.notification_scroll = self.home_screen.findChild(QScrollArea, "notification_scroll")
        self.notification_widget = self.home_screen.findChild(QWidget, "notification_widget")

        self.notification_label = QLabel(self.notification_scroll)
        self.notification_label.setAlignment(Qt.AlignCenter)
        self.notification_label.setMinimumSize(260,80)
        self.notification_label.setWordWrap(True)
        self.notification_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.notification_label.setText(f"Plant paradise - no updates or reminders at the moment.")
        self.notification_label.setStyleSheet(f"background-color:#E9E5E3; font-family: Candara; color: #4F7375; font-size: 12pt; font-style: italic; padding: 10px; border-radius: 10px;")

        self.notification_widget.layout().addWidget(self.notification_label)
        self.notification_scroll.setWidget(self.notification_widget)
        self.notification_widget.layout().setAlignment(QtCore.Qt.AlignTop)


if __name__ == '__main__':

    #app = QApplication([])
    app = QApplication(sys.argv)
    app.setApplicationName("PyFlora")
    login_screen = LoginScreen()
    login_screen.show()
    app.exec_()
