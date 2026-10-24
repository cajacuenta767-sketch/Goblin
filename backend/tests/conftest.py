"""Configuración de pytest: añade backend/ al path para importar los módulos."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
