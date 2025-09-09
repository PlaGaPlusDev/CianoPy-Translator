import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QTextEdit, QProgressBar, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal

# Assuming the core modules are in the parent directory of gui
sys.path.append(sys.path[0] + '/..')
from core.translation_manager import TranslationManager

class TranslationWorker(QObject):
    """Worker thread for running the translation process."""
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    log = pyqtSignal(str)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    def run(self):
        """Starts the translation manager."""
        try:
            manager = TranslationManager(
                self.settings,
                progress_callback=self.progress.emit,
                log_callback=self.log.emit
            )
            manager.run_translation()
        except Exception as e:
            self.log.emit(f"FATAL ERROR in worker thread: {e}")
        finally:
            self.finished.emit()

class MainWindow(QMainWindow):
    """Main window for the Ren'Py Translator application."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ren'Py Translator")
        self.setGeometry(100, 100, 900, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._init_ui()

    def _init_ui(self):
        # Path storage
        self.rpy_files = []
        self.game_folder = ""
        self.renpy_path = ""

        # Create main sections
        self.main_layout.addWidget(self._create_input_section())
        self.main_layout.addWidget(self._create_config_section())
        self.main_layout.addWidget(self._create_options_section())
        self.main_layout.addWidget(self._create_control_section())
        self.main_layout.addWidget(self._create_log_section())

        # Connect signals
        self.load_files_button.clicked.connect(self._open_files)
        self.load_folder_button.clicked.connect(self._open_folder)
        self.translate_button.clicked.connect(self._start_translation)

    def _start_translation(self):
        # 1. Gather settings
        settings = {
            "rpy_files": self.rpy_files,
            "game_folder": self.game_folder,
            "source_lang": self.source_lang_combo.currentText(),
            "target_lang": self.target_lang_combo.currentText(),
            "engine": self.engine_combo.currentText(),
            "api_key": self.api_key_input.text(),
            "multiprocess": self.multiprocess_check.isChecked(),
            "skip_translated": self.skip_translated_check.isChecked(),
            "backup": self.backup_check.isChecked(),
            "replace_symbols": self.replace_symbols_check.isChecked(),
        }

        # 2. Validate settings
        if not self.rpy_files and not self.game_folder:
            QMessageBox.warning(self, "Error", "Por favor, carga al menos un archivo .rpy o una carpeta de juego.")
            return

        engine = settings["engine"]
        if engine in ["DeepL", "Yandex Translate"] and not settings["api_key"]:
            QMessageBox.warning(self, "Error", f"El motor {engine} requiere una clave de API.")
            return

        # 3. Setup and run worker thread
        self.thread = QThread()
        self.worker = TranslationWorker(settings)
        self.worker.moveToThread(self.thread)

        # 4. Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.log.connect(self._append_log)
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._on_translation_finished)

        # 5. Start the thread
        self.thread.start()

        # Disable button during translation
        self.translate_button.setEnabled(False)
        self.log_output.clear()
        self.log_output.append("Iniciando traducción...")

    def _append_log(self, message):
        self.log_output.append(message)

    def _update_progress(self, value):
        self.progress_bar.setValue(value)

    def _on_translation_finished(self):
        self.translate_button.setEnabled(True)
        self.log_output.append("¡Proceso finalizado!")
        QMessageBox.information(self, "Completado", "La traducción ha finalizado.")
        self.progress_bar.setValue(100)

    def _open_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Seleccionar Archivos .rpy", "", "Ren'Py Scripts (*.rpy);;All Files (*)")
        if files:
            self.rpy_files = files
            self.file_input.setText(f"{len(files)} archivos seleccionados")
            self.log_output.append(f"Cargados {len(files)} archivos .rpy.")

    def _open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta del Juego")
        if folder:
            self.game_folder = folder
            self.folder_input.setText(folder)
            self.log_output.append(f"Carpeta del juego seleccionada: {folder}")

    # ... [The rest of the _create_* section methods remain unchanged] ...
    def _create_input_section(self):
        """Creates the group box for data input."""
        group_box = QGroupBox("Sección de Entrada de Datos")
        layout = QVBoxLayout()

        # File selection
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Ruta a los archivos .rpy...")
        self.file_input.setReadOnly(True)
        self.load_files_button = QPushButton("Cargar Archivos .rpy")
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.load_files_button)
        layout.addLayout(file_layout)

        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Ruta a la carpeta del juego...")
        self.folder_input.setReadOnly(True)
        self.load_folder_button = QPushButton("Cargar Carpeta del Juego")
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(self.load_folder_button)
        layout.addLayout(folder_layout)

        group_box.setLayout(layout)
        return group_box

    def _create_config_section(self):
        """Creates the group box for translation configuration."""
        group_box = QGroupBox("Sección de Configuración")
        main_layout = QVBoxLayout()

        # Top layout for language and engine selectors
        top_layout = QHBoxLayout()

        # Source Language
        source_lang_layout = QVBoxLayout()
        source_lang_layout.addWidget(QLabel("Idioma Original"))
        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItems(["Auto", "EN", "ES", "JA", "RU", "ZH"])
        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItems(["ES", "EN", "JA", "RU", "ZH"])
        source_lang_layout.addWidget(self.source_lang_combo)
        top_layout.addLayout(source_lang_layout)

        # Target Language
        target_lang_layout = QVBoxLayout()
        target_lang_layout.addWidget(QLabel("Idioma Objetivo"))
        target_lang_layout.addWidget(self.target_lang_combo)
        top_layout.addLayout(target_lang_layout)

        # Translation Engine
        engine_layout = QVBoxLayout()
        engine_layout.addWidget(QLabel("Motor de Traducción"))
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["Google Translate", "DeepL", "Yandex Translate"])
        engine_layout.addWidget(self.engine_combo)
        top_layout.addLayout(engine_layout)

        main_layout.addLayout(top_layout)

        # Bottom layout for API Key
        api_key_layout = QHBoxLayout()
        self.api_key_label = QLabel("Clave de API (DeepL/Yandex):")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Introduce tu clave de API...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_key_layout.addWidget(self.api_key_label)
        api_key_layout.addWidget(self.api_key_input)
        main_layout.addLayout(api_key_layout)

        group_box.setLayout(main_layout)
        return group_box

    def _create_options_section(self):
        """Creates the group box for additional options."""
        group_box = QGroupBox("Sección de Opciones Adicionales")
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.multiprocess_check = QCheckBox("Traducción multiproceso")
        self.skip_translated_check = QCheckBox("Saltar líneas ya traducidas")
        self.backup_check = QCheckBox("Generar archivos de respaldo (.bak)")
        self.replace_symbols_check = QCheckBox("Habilitar reemplazo de símbolos especiales")
        self.replace_symbols_check.setToolTip("Funcionalidad pendiente: Reemplaza comillas tipográficas y otros símbolos.")

        # Set default states
        self.multiprocess_check.setChecked(True)
        self.skip_translated_check.setChecked(True)
        self.backup_check.setChecked(True)
        self.replace_symbols_check.setChecked(False) # Default to off

        layout.addWidget(self.multiprocess_check)
        layout.addWidget(self.skip_translated_check)
        layout.addWidget(self.backup_check)
        layout.addWidget(self.replace_symbols_check)

        group_box.setLayout(layout)
        return group_box

    def _create_control_section(self):
        """Creates the main control and status widgets."""
        group_box = QGroupBox("Sección de Control y Estado")
        layout = QVBoxLayout()

        # Translate Button
        self.translate_button = QPushButton("TRADUCIR")
        font = self.translate_button.font()
        font.setPointSize(14)
        self.translate_button.setFont(font)
        self.translate_button.setMinimumHeight(40)
        layout.addWidget(self.translate_button)

        # Progress Bar and Status
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("0 de 0 archivos completados")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        layout.addLayout(progress_layout)

        group_box.setLayout(layout)
        return group_box

    def _create_log_section(self):
        """Creates the text area for logging."""
        group_box = QGroupBox("Registro de actividad")
        layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)
        group_box.setLayout(layout)
        return group_box

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
