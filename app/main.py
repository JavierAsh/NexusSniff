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


def get_resource_path(relative_path: str) -> Path:
    """Devuelve la ruta absoluta al recurso, compatible con desarrollo y PyInstaller.
    
    Args:
        relative_path (str): Ruta relativa del recurso dentro de la carpeta 'app/'.
        
    Returns:
        Path: Objeto Path con la ruta absoluta al recurso solicitado.
    """
    try:
        # En PyInstaller (onedir), sys._MEIPASS contiene el directorio _internal.
        # Los datos (*.qss, iconos) se copian a '_internal/app/...'.
        base_path = Path(sys._MEIPASS)
        return base_path / "app" / relative_path
    except Exception:
        # En modo de desarrollo normal (ejecutando desde carpeta fuente)
        return Path(__file__).parent.parent / "app" / relative_path


def _load_theme_content(theme_name: str = "dark") -> str:
    """Lee el contenido QSS del tema SIN aplicarlo a ninguna QApplication.
    
    Args:
        theme_name (str, optional): Nombre del tema a cargar (sin extensión). Defaults to "dark".
        
    Returns:
        str: Cadena con el contenido del archivo QSS, o un string vacío si ocurre un error.
    """
    theme_path = get_resource_path(f"themes/{theme_name}.qss")
    if theme_path.exists():
        try:
            with open(theme_path, 'r', encoding='utf-8') as f:
                return f.read()
        except OSError as e:
            logger.error("Error al leer el tema %s: %s", theme_path, e)
    return ""


def load_theme(app: QApplication, theme_name: str = "dark") -> str:
    """Carga la hoja de estilos y la aplica a la QApplication.
    
    Args:
        app (QApplication): La instancia de la aplicación PyQt6.
        theme_name (str, optional): Nombre del tema a cargar. Defaults to "dark".
        
    Returns:
        str: Contenido del tema QSS cargado, util para debugging.
    """
    content = _load_theme_content(theme_name)
    if content:
        app.setStyleSheet(content)
        logger.info("Tema cargado: %s", theme_name)
    else:
        logger.warning("No se encontró el tema: %s", theme_name)
    return content


def main():
    """Punto de entrada principal de NexusSniff.
    
    Inicializa el logger, aplica configuraciones globales como High DPI, 
    crea la ventana inicial (Splash Screen) mientras carga el motor,
    instancia la MainWindow principal, aplica los estilos e inicia el event loop.
    
    Raises:
        SystemExit: Cuando la ventana principal se cierra o termina el event loop.
    """
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="[NexusSniff] %(levelname)s — %(name)s — %(message)s"
    )

    # Habilitar High DPI
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("NexusSniff")
    app.setApplicationVersion("1.4.0-beta.1")
    app.setOrganizationName("NexusSniff")

    # Instalar crash reporter global (antes de todo lo demás)
    from app.ui.crash_dialog import install_exception_hook
    install_exception_hook()

    # Cargar preferencias desde QSettings
    from PyQt6.QtCore import QSettings
    settings = QSettings("NexusSniff", "NexusSniff")
    current_theme = settings.value("theme", "dark")

    # Icono global de la aplicación
    logo_path = get_resource_path("resources/icons/logo.png")
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

    # Se eliminó la aplicación temprana del tema; se aplicará DESPUÉS de instanciar MainWindow.
    # --- Pantalla de Carga (Splash Screen) ---
    from PyQt6.QtWidgets import QSplashScreen
    from PyQt6.QtGui import QPixmap
    import time

    # Preferir splash.png (fondo transparente) sobre logo.png
    splash_path = get_resource_path("resources/icons/splash.png")
    if splash_path.exists():
        splash_pix = QPixmap(str(splash_path))
    elif logo_path.exists():
        splash_pix = QPixmap(str(logo_path))
    else:
        splash_pix = QPixmap()

    # Escalar a un tamaño adecuado para splash
    if not splash_pix.isNull():
        splash_pix = splash_pix.scaled(
            420, 420,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    splash = QSplashScreen(
        splash_pix,
        Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint,
    )
    # Fondo translúcido: Qt NO dibuja el rectángulo blanco detrás de los
    # píxeles transparentes del QPixmap.
    splash.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    splash.show()
    app.processEvents()

    # Cerrar splash nativo de PyInstaller si el ejecutable lo soporta
    try:
        import pyi_splash          # type: ignore[import-untyped]
        pyi_splash.close()
    except ImportError:
        pass

    splash.showMessage(
        "Cargando motor de captura…",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        Qt.GlobalColor.white,
    )
    app.processEvents()

    # Crear y mostrar la ventana principal (esto es lo que más tarda)
    from app.ui.main_window import MainWindow
    window = MainWindow()

    window.show()

    # Aplicar el tema DESPUES de mostrar la ventana principal (window.show()).
    # Esto asegura que PyQt6 ya ha inicializado todos los HWND nativos y polimorfismos,
    # resolviendo el bug donde la interfaz aparecía sin estilo.
    load_theme(app, theme_file)

    # Mantener el splash por 1 segundo extra dentro del event loop
    # para asegurar que la ventana se ha renderizado por completo
    from PyQt6.QtCore import QTimer
    QTimer.singleShot(1000, lambda: splash.finish(window))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
