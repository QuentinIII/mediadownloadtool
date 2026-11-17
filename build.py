#!/usr/bin/env python3
"""
Construit l'exécutable portable (un seul fichier) avec PyInstaller.
ffmpeg et Deno sont embarqués dans l'exe : rien à installer chez l'utilisateur.

    pip install -r requirements.txt pyinstaller
    python build.py            ->  dist/mediadownloadtool(.exe)
"""
import os
import sys
import shutil
import subprocess

import deno
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
WIN = sys.platform.startswith("win")
EXT = ".exe" if WIN else ""
SEP = ";" if WIN else ":"

stage = os.path.join(HERE, "build", "bin")
shutil.rmtree(stage, ignore_errors=True)
os.makedirs(stage)

ffmpeg_src = imageio_ffmpeg.get_ffmpeg_exe()
deno_src = deno.find_deno_bin()
for src, name in ((ffmpeg_src, "ffmpeg"), (deno_src, "deno")):
    if not src or not os.path.isfile(src):
        sys.exit(f"{name} introuvable : {src}")
    dst = os.path.join(stage, name + EXT)
    shutil.copy2(src, dst)
    print(f"{name}: {src} -> {dst}")

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm", "--clean", "--onefile", "--windowed",
    "--name", "mediadownloadtool",
    "--add-binary", f"{os.path.join(stage, 'ffmpeg' + EXT)}{SEP}bin",
    "--add-binary", f"{os.path.join(stage, 'deno' + EXT)}{SEP}bin",
    "--collect-all", "yt_dlp_ejs",
    "--collect-submodules", "yt_dlp",
    "--hidden-import", "mutagen",
    "--hidden-import", "Cryptodome",
    "--hidden-import", "brotli",
    "--hidden-import", "certifi",
    "--hidden-import", "websockets",
    "--exclude-module", "imageio_ffmpeg",
    os.path.join(HERE, "mediadownloadtool.py"),
]
print(" ".join(cmd))
subprocess.check_call(cmd, cwd=HERE)
print("OK ->", os.path.join(HERE, "dist", "mediadownloadtool" + EXT))
