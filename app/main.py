"""
main.py — Punto de entrada de NexusSniff.

Inicializa la aplicación QApplication, carga el tema QSS,
y lanza la ventana principal.
"""

import sys
import os
import logging
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase, QIcon
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


def _load_theme_content(theme_name: str = "dark") -> str:
    """Lee el contenido QSS del tema SIN aplicarlo a ninguna QApplication.
    Usado para previews dentro del diálogo de configuración."""
    theme_path = Path(__file__).parent / "themes" / f"{theme_name}.qss"
    if theme_path.exists():
        try:
            with open(theme_path, 'r', encoding='utf-8') as f:
                return f.read()
        except OSError as e:
            logger.error("Error al leer el tema %s: %s", theme_path, e)
    return ""


def load_theme(app: QApplication, theme_name: str = "dark") -> str:
    """Carga la hoja de estilos y la aplica a la QApplication."""
    content = _load_theme_content(theme_name)
    if content:
        app.setStyleSheet(content)
        logger.info("Tema cargado: %s", theme_name)
    else:
        logger.warning("No se encontró el tema: %s", theme_name)
    return content


def main():
    """Punto de entrada principal."""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="[NexusSniff] %(levelname)s — %(name)s — %(message)s"
    )

    # Habilitar High DPI
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("NexusSniff")
    app.setApplicationVersion("1.2.0")
    app.setOrganizationName("NexusSniff")

    # Instalar crash reporter global (antes de todo lo demás)
    from app.ui.crash_dialog import install_exception_hook
    install_exception_hook()

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

    # Resolver el nombre del tema (guardar valor interno, no texto display)
    if isinstance(current_theme, str) and "light" in current_theme.lower():
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
