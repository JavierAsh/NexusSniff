"""
main.py — Punto de entrada de NexusSniff.

Inicializa la aplicación QApplication, carga el tema QSS,
y lanza la ventana principal.
"""

import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase, QIcon
from PyQt6.QtCore import Qt


def load_theme(app: QApplication, theme_name: str = "dark") -> str:
    """Carga la hoja de estilos."""
    theme_path = Path(__file__).parent / "themes" / f"{theme_name}.qss"

    if theme_path.exists():
        with open(theme_path, 'r', encoding='utf-8') as f:
            content = f.read()
            app.setStyleSheet(content)
            print(f"[NexusSniff] Tema cargado: {theme_name}")
            return content
    else:
        print(f"[NexusSniff] Advertencia: No se encontró {theme_path}")
        return ""


def main():
    """Punto de entrada principal."""
    # Habilitar High DPI
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("NexusSniff")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("NexusSniff")

    # Cargar preferencias desde QSettings
    from PyQt6.QtCore import QSettings
    settings = QSettings("NexusSniff", "NexusSniff")
    current_theme = settings.value("theme", "dark")

    # Icono global de la aplicación
    logo_path = Path(__file__).parent / "resources" / "icons" / "logo.png"
    if logo_path.exists():
        app.setWindowIcon(QIcon(str(logo_path)))

    # Fuente global
    default_font = QFont("Segoe UI", 13)
    default_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(default_font)

    # Manejar los nombres amigables del combobox si están guardados así
    if "Light Mode" in current_theme:
        theme_file = "light"
    else:
        theme_file = "dark"

    load_theme(app, theme_file)

    # Crear y mostrar la ventana principal
    from app.ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
