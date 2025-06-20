import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QLabel, QComboBox, QTabWidget,
                             QFrame, QGridLayout, QScrollArea, QSplitter,
                             QDialog, QTextEdit, QMessageBox, QLineEdit, QFileDialog,
                             QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor, QIcon
import requests
from io import BytesIO
import json
import os
import subprocess
import time

class UpdateThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def run(self):
        try:
            scripts = [
                ('scripts/CsvConvert.py', "Fetching latest launch data..."),
                ('scripts/rocket_analysis.py', "Fetching rocket details..."),
                ('scripts/download_rocket_images.py', "Downloading rocket images...")
            ]
            total_steps = len(scripts)

            for i, (script, message) in enumerate(scripts):
                self.progress.emit(int((i / total_steps) * 100), message)
                
                process = subprocess.Popen(['python', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    error_message = f"Error running {script}:\\n{stderr}"
                    self.finished.emit(False, error_message)
                    return
            
            self.progress.emit(100, "Update complete!")
            time.sleep(1) # Kullanıcının mesajı görmesi için kısa bir bekleme
            self.finished.emit(True, "All data has been updated successfully.")

        except Exception as e:
            self.finished.emit(False, f"An unexpected error occurred: {e}")

class ModernButton(QPushButton):
    def __init__(self, text, color="#3a86ff"):
        super().__init__(text)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: none;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #5d9aff;
            }}
            QPushButton:pressed {{
                background-color: #2c6fcc;
            }}
        """)

class RocketDetailDialog(QDialog):
    photo_changed = pyqtSignal()

    def __init__(self, launch_id, rocket_info, parent=None):
        super().__init__(parent)
        self.launch_id = launch_id
        self.rocket_info = rocket_info
        self.parent_gui = parent
        self.setWindowTitle(f"🚀 {self.rocket_info['name']} - Details")
        self.setGeometry(200, 200, 800, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #0d1117;
                color: #c9d1d9;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel(f"🚀 {self.rocket_info['name']}")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #3a86ff; margin: 20px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Content
        content_layout = QHBoxLayout()
        
        # Left: Image
        image_frame = QFrame()
        image_frame.setStyleSheet("background-color: #161b22; border-radius: 12px; padding: 20px; margin: 10px; border: 1px solid #30363d;")
        image_layout = QVBoxLayout(image_frame)
        
        self.image_label = QLabel()
        self.load_launch_image()
        
        # Resmi değiştir butonu
        change_image_btn = ModernButton("Change Launch Image", "#3a86ff")
        change_image_btn.clicked.connect(self.change_launch_image)
        image_layout.addWidget(change_image_btn)

        image_layout.addWidget(self.image_label)
        content_layout.addWidget(image_frame)
        
        # Right: Details
        details_frame = QFrame()
        details_frame.setStyleSheet("background-color: #161b22; border-radius: 12px; padding: 20px; margin: 10px; border: 1px solid #30363d;")
        details_layout = QVBoxLayout(details_frame)
        
        details_text = f"""
        <h3 style="color: #3a86ff; margin-bottom: 15px;">Technical Specifications</h3>
        
        <table style="width: 100%; border-collapse: collapse;">
        <tr><td style="padding: 8px; font-weight: bold; color: #8b949e;">Type:</td><td style="padding: 8px;">{self.rocket_info['type']}</td></tr>
        <tr><td style="padding: 8px; font-weight: bold; color: #8b949e;">Status:</td><td style="padding: 8px;">{'🟢 Active' if self.rocket_info['active'] else '🔴 Inactive'}</td></tr>
        <tr><td style="padding: 8px; font-weight: bold; color: #8b949e;">Success Rate:</td><td style="padding: 8px;">%{self.rocket_info['success_rate_pct']}</td></tr>
        <tr><td style="padding: 8px; font-weight: bold; color: #8b949e;">First Flight:</td><td style="padding: 8px;">{self.rocket_info['first_flight']}</td></tr>
        <tr><td style="padding: 8px; font-weight: bold; color: #8b949e;">Cost per Launch:</td><td style="padding: 8px;">${self.rocket_info['cost_per_launch']:,}</td></tr>
        </table>
        
        <h4 style="color: #3a86ff; margin-top: 20px; margin-bottom: 10px;">Description</h4>
        <p style="line-height: 1.6; color: #c9d1d9;">{self.rocket_info['description']}</p>
        """
        
        details_label = QLabel(details_text)
        details_label.setWordWrap(True)
        details_layout.addWidget(details_label)
        
        content_layout.addWidget(details_frame)
        layout.addLayout(content_layout)
        
        # Close button
        close_btn = ModernButton("Close", "#c93c37")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
    def load_launch_image(self):
        pixmap = QPixmap()
        image_loaded = False
        
        # 1. Fırlatmaya özel resmi kontrol et
        launch_image_path = self.parent_gui.get_launch_specific_image(self.launch_id)
        if launch_image_path and os.path.exists(launch_image_path):
            if pixmap.load(launch_image_path):
                image_loaded = True
        
        # 2. Roketin genel resmini kontrol et
        if not image_loaded:
            rocket_image_path = self.parent_gui.get_rocket_image_path(self.rocket_info['name'])
            if rocket_image_path and os.path.exists(rocket_image_path):
                if pixmap.load(rocket_image_path):
                    image_loaded = True

        # 3. Varsayılan kullanıcı resmini kontrol et
        if not image_loaded:
            fallback_image_path = "assets/M3k.jpg"
            if os.path.exists(fallback_image_path):
                if pixmap.load(fallback_image_path):
                    image_loaded = True

        if image_loaded:
            pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("Image not found")
            self.image_label.setStyleSheet("font-size: 24px; text-align: center; color: #c93c37;")

    def change_launch_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image for Launch", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.parent_gui.save_launch_specific_image(self.launch_id, file_path)
            self.load_launch_image() # Resmi yeniden yükle
            self.photo_changed.emit() # Ana GUI'ye sinyal gönder

    def get_rocket_image_path(self, rocket_name):
        rocket_folder = f"assets/images/{rocket_name.replace(' ', '_')}"
        if os.path.exists(rocket_folder):
            # Özel dosya isimleri için kontrol
            if rocket_name == "Falcon 1":
                specific_file = os.path.join(rocket_folder, "UserView-1.jpg")
                if os.path.exists(specific_file):
                    return specific_file
            elif rocket_name == "Falcon 9":
                specific_file = os.path.join(rocket_folder, "image_6.jpg")
                if os.path.exists(specific_file):
                    return specific_file
            
            # Genel dosya arama (fallback)
            for file in os.listdir(rocket_folder):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    return os.path.join(rocket_folder, file)
        return None

class SpaceXGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 SpaceX Launch Analysis Dashboard")
        self.setGeometry(100, 100, 1600, 950)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0d1117;
                color: #c9d1d9;
            }
            QTabWidget::pane {
                border: 1px solid #30363d;
                background-color: #161b22;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #161b22;
                color: #8b949e;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                border: 1px solid #30363d;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #3a86ff;
                color: white;
                border-color: #3a86ff;
            }
            QTableWidget {
                background-color: #0d1117;
                color: #c9d1d9;
                gridline-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #21262d;
            }
            QTableWidget::item:selected {
                background-color: #3a86ff40;
                color: #58a6ff;
            }
            QHeaderView::section {
                background-color: #161b22;
                color: #8b949e;
                padding: 12px;
                border: 1px solid #30363d;
                font-weight: bold;
            }
            QComboBox {
                background-color: #161b22;
                color: #c9d1d9;
                border: 2px solid #30363d;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #8b949e;
            }
            QComboBox:hover {
                border: 2px solid #3a86ff;
            }
            QLabel {
                color: #c9d1d9;
            }
            QFrame#StatCard {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 12px;
                padding: 20px;
                margin: 8px;
            }
            QFrame#StatCard:hover {
                border-color: #3a86ff;
            }
        """)
        
        # Load data
        self.df = pd.read_csv('data/spacex_launches.csv')
        self.df['date_utc'] = pd.to_datetime(self.df['date_utc'], errors='coerce')
        self.df = self.df.dropna(subset=['date_utc'])
        self.df['year'] = self.df['date_utc'].dt.year
        
        # Load rocket info
        self.load_rocket_info()
        self.load_launch_images_db() # Fırlatma resim veritabanını yükle
        self.filtered_df = self.df.copy() # Filtrelenmiş DataFrame için
        
        # Matplotlib style
        plt.style.use('dark_background')
        
        self.init_ui()
        
    def load_rocket_info(self):
        try:
            with open('data/rockets_info.json', 'r', encoding='utf-8') as f:
                self.rockets_info = json.load(f)
        except:
            self.rockets_info = []
        
    def load_launch_images_db(self):
        self.launch_images_db_path = 'data/launch_images.json'
        try:
            with open(self.launch_images_db_path, 'r', encoding='utf-8') as f:
                self.launch_images = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.launch_images = {} # { "launch_id": "path/to/image.jpg" }

    def save_launch_specific_image(self, launch_id, image_path):
        self.launch_images[launch_id] = image_path
        try:
            with open(self.launch_images_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.launch_images, f, indent=2)
            QMessageBox.information(self, "Success", "Launch image has been updated.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save launch image database: {e}")

    def get_launch_specific_image(self, launch_id):
        return self.launch_images.get(launch_id)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(25, 25, 25, 25)
        
        # Header
        header_layout = QHBoxLayout()
        self.create_header(header_layout)
        main_layout.addLayout(header_layout)
        
        # Body
        body_layout = QHBoxLayout()
        main_layout.addLayout(body_layout, 1)
        
        # Left Panel (Tabs)
        tabs = QTabWidget()
        self.create_data_tab(tabs)
        self.create_charts_tab(tabs)
        self.create_rocket_gallery_tab(tabs)
        self.create_settings_tab(tabs)
        self.tabs = tabs # Sekmelere erişim için referans
        body_layout.addWidget(self.tabs, 3) # Takes 75% of space
        
        # Right Panel (Stats)
        stats_frame = QFrame()
        self.stats_layout = QVBoxLayout(stats_frame)
        self.create_stat_cards(self.stats_layout)
        self.stats_layout.addStretch()
        body_layout.addWidget(stats_frame, 1) # Takes 25% of space

    def create_header(self, layout):
        # Logo placeholder
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        
        # Sol taraf - Logo ve başlık
        left_section = QHBoxLayout()
        
        logo_label = QLabel()
        logo_path = "assets/M3k.jpg"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label.setPixmap(pixmap)
            else:
                logo_label.setText("🚀")
                logo_label.setStyleSheet("font-size: 60px;")
        else:
            logo_label.setText("🚀")
            logo_label.setStyleSheet("font-size: 60px;")
        
        logo_label.setFixedSize(80, 80)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet(logo_label.styleSheet() + "background-color: #161b22; border-radius: 40px; padding: 5px;")
        
        title = QLabel("SpaceX Launch Analysis Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #58a6ff; margin-left: 15px;")
        
        left_section.addWidget(logo_label)
        left_section.addWidget(title)
        left_section.addStretch()
        
        header_layout.addLayout(left_section)
        
        layout.addWidget(header_frame)

    def create_stat_cards(self, layout):
        total_launches = len(self.df)
        success_launches = len(self.df[self.df['success'] == True])
        success_rate = (success_launches / total_launches) * 100 if total_launches > 0 else 0
        
        stats = [
            ("Total Launches", str(total_launches), "#3a86ff"),
            ("Successful Launches", str(success_launches), "#23c552"),
            ("Success Rate", f"{success_rate:.1f}%", "#e69b00"),
            ("First Launch", str(self.df['year'].min()), "#e14a4a")
        ]
        
        for title, value, color in stats:
            card = QFrame()
            card.setObjectName("StatCard")
            card_layout = QVBoxLayout(card)
            
            value_label = QLabel(value)
            value_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
            value_label.setAlignment(Qt.AlignCenter)

            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 13px; color: #8b949e; font-weight: bold;")
            title_label.setAlignment(Qt.AlignCenter)
            
            card_layout.addWidget(value_label)
            card_layout.addWidget(title_label)
            
            layout.addWidget(card)
        
    def create_data_tab(self, tabs):
        data_widget = QWidget()
        layout = QVBoxLayout(data_widget)
        
        # Filtering controls
        filter_frame = QFrame()
        filter_frame.setStyleSheet("background-color: transparent; border: none;")
        filter_layout = QHBoxLayout(filter_frame)
        
        # Arama kutusu
        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-weight: bold; margin-right: 10px; color: #8b949e;")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by mission name...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #161b22;
                color: #c9d1d9;
                border: 2px solid #30363d;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #3a86ff;
            }
        """)
        self.search_box.textChanged.connect(self.filter_data)
        
        # Yıl filtresi
        year_label = QLabel("Year:")
        year_label.setStyleSheet("font-weight: bold; margin-right: 10px; margin-left: 20px; color: #8b949e;")
        self.year_combo = QComboBox()
        years = sorted(self.df['year'].unique())
        self.year_combo.addItem("All")
        self.year_combo.addItems([str(year) for year in years])
        self.year_combo.currentTextChanged.connect(self.filter_data)
        
        # Success filter
        success_label = QLabel("Success:")
        success_label.setStyleSheet("font-weight: bold; margin-right: 10px; margin-left: 30px; color: #8b949e;")
        self.success_combo = QComboBox()
        self.success_combo.addItems(["All", "Successful", "Failed"])
        self.success_combo.currentTextChanged.connect(self.filter_data)
        
        filter_layout.addWidget(search_label)
        filter_layout.addWidget(self.search_box)
        filter_layout.addWidget(year_label)
        filter_layout.addWidget(self.year_combo)
        filter_layout.addWidget(success_label)
        filter_layout.addWidget(self.success_combo)
        
        # Dışa aktarma butonu
        export_btn = ModernButton("Export Data", "#16a34a")
        export_btn.clicked.connect(self.export_data)
        filter_layout.addWidget(export_btn)
        
        filter_layout.addStretch()
        
        layout.addWidget(filter_frame)
        
        # Table
        self.table = QTableWidget()
        self.table.itemDoubleClicked.connect(self.show_launch_details)
        layout.addWidget(self.table)
        
        # Load data
        self.load_table_data()
        
        tabs.addTab(data_widget, "Launch Data")
        
    def create_charts_tab(self, tabs):
        charts_widget = QWidget()
        layout = QVBoxLayout(charts_widget)
        
        # Chart selection
        chart_frame = QFrame()
        chart_frame.setObjectName("StatCard")
        chart_layout = QHBoxLayout(chart_frame)
        
        chart_label = QLabel("Select Chart:")
        chart_label.setStyleSheet("font-weight: bold; margin-right: 10px; color: #8b949e;")
        self.chart_combo = QComboBox()
        self.chart_combo.addItems([
            "Launches per Year",
            "Success/Failure Distribution", 
            "Success Rate by Year"
        ])
        self.chart_combo.currentTextChanged.connect(self.show_chart)
        
        chart_layout.addWidget(chart_label)
        chart_layout.addWidget(self.chart_combo)
        chart_layout.addStretch()
        
        layout.addWidget(chart_frame)
        
        # Chart display
        self.figure = Figure(figsize=(12, 8), facecolor='#161b22')
        self.canvas = FigureCanvas(self.figure)
        self.figure.canvas.mpl_connect('pick_event', self.on_pick)
        layout.addWidget(self.canvas)
        
        tabs.addTab(charts_widget, "Charts")
        
    def create_rocket_gallery_tab(self, tabs):
        gallery_widget = QWidget()
        layout = QVBoxLayout(gallery_widget)
        
        title = QLabel("Rocket Gallery")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #58a6ff; margin: 15px;")
        layout.addWidget(title)
        
        # Scroll area for rockets
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_widget = QWidget()
        scroll_layout = QGridLayout(scroll_widget)
        
        # Load rocket images
        for i, rocket in enumerate(self.rockets_info):
            rocket_frame = QFrame()
            rocket_frame.setObjectName("StatCard")
            rocket_layout = QVBoxLayout(rocket_frame)
            
            # Rocket image
            image_label = QLabel()
            image_path = self.get_rocket_image_path(rocket['name'])
            
            pixmap = QPixmap()
            image_loaded = False
            
            if image_path and os.path.exists(image_path):
                if pixmap.load(image_path):
                    image_loaded = True
            
            if not image_loaded:
                fallback_image_path = "assets/M3k.jpg"
                if os.path.exists(fallback_image_path):
                    if pixmap.load(fallback_image_path):
                        image_loaded = True
            
            if image_loaded:
                pixmap = pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_label.setPixmap(pixmap)
            else:
                image_label.setText("Image not found")
                image_label.setStyleSheet("font-size: 16px; text-align: center; color: #c93c37;")
            
            image_label.setAlignment(Qt.AlignCenter)
            rocket_layout.addWidget(image_label)
            
            # Rocket name
            name_label = QLabel(rocket['name'])
            name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #c9d1d9; text-align: center;")
            rocket_layout.addWidget(name_label)
            
            # Rocket type
            type_label = QLabel(f"Type: {rocket['type']}")
            type_label.setStyleSheet("font-size: 12px; color: #8b949e; text-align: center;")
            rocket_layout.addWidget(type_label)
            
            # Status
            status = "Active" if rocket['active'] else "Inactive"
            status_color = "#1d914b" if rocket['active'] else "#c93c37"
            status_label = QLabel(f"Status: {status}")
            status_label.setStyleSheet(f"font-size: 12px; color: {status_color}; text-align: center;")
            rocket_layout.addWidget(status_label)
            
            scroll_layout.addWidget(rocket_frame, i // 3, i % 3)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        tabs.addTab(gallery_widget, "Rocket Gallery")
        
    def create_settings_tab(self, tabs):
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("Application Settings")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #58a6ff; margin: 15px;")
        layout.addWidget(title)

        # Veri güncelleme bölümü
        update_frame = QFrame()
        update_frame.setObjectName("StatCard")
        update_layout = QVBoxLayout(update_frame)
        
        update_title = QLabel("Update Application Data")
        update_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #c9d1d9; margin-bottom: 10px;")
        
        update_desc = QLabel("Fetch the latest launch and rocket data from the SpaceX API. This may take a few moments.")
        update_desc.setWordWrap(True)
        update_desc.setStyleSheet("color: #8b949e; margin-bottom: 20px;")
        
        self.update_btn = ModernButton("Update Data Now", "#1d914b")
        self.update_btn.clicked.connect(self.start_update_process)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        
        update_layout.addWidget(update_title)
        update_layout.addWidget(update_desc)
        update_layout.addWidget(self.update_btn)
        update_layout.addWidget(self.progress_bar)
        update_layout.addWidget(self.progress_label)

        layout.addWidget(update_frame)
        
        # Kapatma bölümü
        close_frame = QFrame()
        close_frame.setObjectName("StatCard")
        close_layout = QVBoxLayout(close_frame)
        
        close_title = QLabel("Application Control")
        close_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #c9d1d9; margin-bottom: 10px;")
        
        close_desc = QLabel("Close the application when you're done analyzing the data.")
        close_desc.setWordWrap(True)
        close_desc.setStyleSheet("color: #8b949e; margin-bottom: 20px;")
        
        close_btn = ModernButton("Close Application", "#c93c37")
        close_btn.clicked.connect(self.close)
        
        close_layout.addWidget(close_title)
        close_layout.addWidget(close_desc)
        close_layout.addWidget(close_btn)

        layout.addWidget(close_frame)
        tabs.addTab(settings_widget, "Settings")

    def start_update_process(self):
        self.update_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        
        self.update_thread = UpdateThread()
        self.update_thread.progress.connect(self.update_progress)
        self.update_thread.finished.connect(self.update_finished)
        self.update_thread.start()

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)

    def update_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.update_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.reload_data()
        else:
            QMessageBox.critical(self, "Error", message)

    def reload_data(self):
        # Veriyi yeniden yükle
        self.df = pd.read_csv('data/spacex_launches.csv')
        self.df['date_utc'] = pd.to_datetime(self.df['date_utc'], errors='coerce')
        self.df = self.df.dropna(subset=['date_utc'])
        self.df['year'] = self.df['date_utc'].dt.year
        self.load_rocket_info()
        self.load_launch_images_db() # Fırlatma resim veritabanını yükle
        self.filtered_df = self.df.copy() # Filtrelenmiş DataFrame için
        
        # Tabloyu yenile
        self.load_table_data()
        
        # İstatistik kartlarını yenile
        # (Bu kısım için kartları silip yeniden oluşturmak en temiz yol)
        for i in reversed(range(self.stats_layout.count())): 
            self.stats_layout.itemAt(i).widget().setParent(None)
        self.create_stat_cards(self.stats_layout)
        
        # Filtreleri sıfırla
        self.search_box.clear()
        self.year_combo.setCurrentIndex(0)
        self.success_combo.setCurrentIndex(0)

        QMessageBox.information(self, "Reloaded", "Application data has been reloaded.")

    def get_rocket_image_path(self, rocket_name):
        rocket_folder = f"assets/images/{rocket_name.replace(' ', '_')}"
        if os.path.exists(rocket_folder):
            # Özel dosya isimleri için kontrol
            if rocket_name == "Falcon 1":
                specific_file = os.path.join(rocket_folder, "UserView-1.jpg")
                if os.path.exists(specific_file):
                    return specific_file
            elif rocket_name == "Falcon 9":
                specific_file = os.path.join(rocket_folder, "image_6.jpg")
                if os.path.exists(specific_file):
                    return specific_file
            
            # Genel dosya arama (fallback)
            for file in os.listdir(rocket_folder):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    return os.path.join(rocket_folder, file)
        return None

    def on_pick(self, event):
        artist = event.artist
        
        # Yıllara Göre Fırlatma Sayıları Grafiği (Bar Chart)
        if isinstance(artist, plt.Rectangle):
            try:
                # Tıklanan bar'ın indeksini al (bu, bar listesindeki pozisyonudur)
                bar_index = artist.get_x() + artist.get_width() / 2
                
                # launch_counts verisinden bu indekse karşılık gelen yılı bul
                if hasattr(self, 'launch_counts_for_chart'):
                    year = self.launch_counts_for_chart.index[int(round(bar_index))]
                    
                    self.tabs.setCurrentIndex(0)
                    index = self.year_combo.findText(str(year))
                    if index != -1:
                        self.year_combo.setCurrentIndex(index)
                        QMessageBox.information(self, "Filter Applied", f"Table filtered for the year {year}.")

            except (ValueError, TypeError, IndexError):
                pass
                
        # Başarı/Başarısız Dağılımı Grafiği (Pie Chart)
        elif isinstance(artist, plt.matplotlib.patches.Wedge):
            gid = artist.get_gid()
            if gid in ['success_wedge', 'failure_wedge']:
                self.tabs.setCurrentIndex(0)
                status = "Successful" if gid == 'success_wedge' else "Failed"
                index = self.success_combo.findText(status)
                if index != -1:
                    self.success_combo.setCurrentIndex(index)
                    QMessageBox.information(self, "Filter Applied", f"Table filtered for {status} launches.")
        
    def show_chart(self, chart_type):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        ax.set_facecolor('#161b22')
        [t.set_color('#8b949e') for t in ax.get_xticklabels()]
        [t.set_color('#8b949e') for t in ax.get_yticklabels()]
        ax.xaxis.label.set_color('#8b949e')
        ax.yaxis.label.set_color('#8b949e')
        ax.title.set_color('#c9d1d9')

        if chart_type == "Launches per Year":
            self.launch_counts_for_chart = self.df['year'].value_counts().sort_index()
            bars = self.launch_counts_for_chart.plot(kind='bar', ax=ax, color='#3a86ff')
            
            # Her bir bar'ı tıklanabilir yap
            for bar in bars.patches:
                bar.set_picker(True)

            ax.set_title('Launches per Year', pad=20, fontsize=16, color="#c9d1d9")
            ax.set_xlabel('Year', labelpad=15, color="#8b949e")
            ax.set_ylabel('Number of Launches', labelpad=15, color="#8b949e")
            
        elif chart_type == "Success/Failure Distribution":
            success_counts = self.df['success'].value_counts()
            labels = ['Successful' if success_counts.index[i] else 'Failed' for i in range(len(success_counts))]
            colors = ['#1d914b' if 'Success' in l else '#c93c37' for l in labels]
            wedges, texts, autotexts = ax.pie(success_counts, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, 
                   wedgeprops=dict(width=0.4, edgecolor='w'))
            
            # Tıklama için ID ata
            for i, wedge in enumerate(wedges):
                wedge.set_picker(True)
                if 'Success' in labels[i]:
                    wedge.set_gid('success_wedge')
                else:
                    wedge.set_gid('failure_wedge')

            ax.set_title('Success vs. Failure Distribution', pad=20, fontsize=16, color="#c9d1d9")
            ax.axis('equal')

        elif chart_type == "Success Rate by Year":
            yearly_success = self.df.groupby('year')['success'].mean() * 100
            yearly_success.plot(kind='line', marker='o', color='#3a86ff', ax=ax)
            ax.set_title('Success Rate by Year (%)', pad=20, fontsize=16, color="#c9d1d9")
            ax.set_xlabel('Year', labelpad=15, color="#8b949e")
            ax.set_ylabel('Success Rate (%)', labelpad=15, color="#8b949e")
            ax.set_ylim(0, 100)

        ax.grid(True, linestyle='--', alpha=0.2)
        self.figure.tight_layout()
        self.canvas.draw()

    def load_table_data(self, filtered_df=None):
        if filtered_df is None:
            filtered_df = self.df
        
        columns = ['name', 'date_utc', 'flight_number', 'success', 'rocket', 'launchpad']
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(['Mission Name', 'Date', 'Flight No', 'Success', 'Rocket ID', 'Launchpad ID'])
        
        self.table.setRowCount(len(filtered_df))
        for i, (idx, row) in enumerate(filtered_df.iterrows()):
            self.table.setItem(i, 0, QTableWidgetItem(str(row['name'])))
            self.table.setItem(i, 1, QTableWidgetItem(str(row['date_utc'].date())))
            self.table.setItem(i, 2, QTableWidgetItem(str(row['flight_number'])))
            
            success_item = QTableWidgetItem("✅" if row['success'] else "❌")
            success_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 3, success_item)
            
            self.table.setItem(i, 4, QTableWidgetItem(str(row['rocket'])))
            self.table.setItem(i, 5, QTableWidgetItem(str(row['launchpad'])))
        
        self.table.resizeColumnsToContents()
        
    def show_launch_details(self, item):
        row = item.row()
        
        if row < len(self.filtered_df):
            launch_data = self.filtered_df.iloc[row]
            launch_id = launch_data['id']
            rocket_id = launch_data['rocket']
            
            rocket_info = next((r for r in self.rockets_info if r['id'] == rocket_id), None)
            
            if rocket_info:
                dialog = RocketDetailDialog(launch_id, rocket_info, self)
                dialog.exec_()
            else:
                QMessageBox.information(self, "Info", "Rocket information not available for this launch.")
        else:
            QMessageBox.critical(self, "Error", "Could not retrieve data for the selected row. Please try again.")
        
    def filter_data(self):
        self.filtered_df = self.df.copy()

        # Arama filtresi
        search_term = self.search_box.text().lower()
        if search_term:
            self.filtered_df = self.filtered_df[self.filtered_df['name'].str.lower().str.contains(search_term)]
        
        # Yıl filtresi
        if self.year_combo.currentText() != "All":
            year = int(self.year_combo.currentText())
            self.filtered_df = self.filtered_df[self.filtered_df['year'] == year]
        
        # Başarı filtresi
        if self.success_combo.currentText() == "Successful":
            self.filtered_df = self.filtered_df[self.filtered_df['success'] == True]
        elif self.success_combo.currentText() == "Failed":
            self.filtered_df = self.filtered_df[self.filtered_df['success'] == False]
            
        self.load_table_data(self.filtered_df)
        
    def export_data(self):
        # Önce mevcut filtrelenmiş veriyi al
        if self.filtered_df.empty:
            QMessageBox.information(self, "No Data", "There is no data to export.")
            return

        # Dosya kaydetme diyaloğunu aç
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Data", "spacex_filtered_data.csv", "CSV Files (*.csv);;All Files (*)")
        
        if file_path:
            try:
                self.filtered_df.to_csv(file_path, index=False, encoding='utf-8')
                QMessageBox.information(self, "Success", f"Data successfully exported to:\\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while exporting data:\\n{e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SpaceXGUI()
    window.show()
    sys.exit(app.exec_()) 