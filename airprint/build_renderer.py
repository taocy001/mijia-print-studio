"""Build the macOS PDF and raster renderer."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[1]
(root/'build').mkdir(exist_ok=True)
subprocess.run(['xcrun','clang++','-std=c++17','-dynamiclib','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations','-framework','CoreGraphics','-framework','CoreFoundation','-lcups',str(root/'airprint/native/document_renderer.cpp'),'-o',str(root/'build/libmijia_render.dylib')],check=True)
