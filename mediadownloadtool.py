#!/usr/bin/env python3
"""
mediadownloadtool — YouTube (et autres sites) -> MP3 / MP4  (interface graphique)
https://github.com/QuentinIII/mediadownloadtool
- Installe tout seul ses dépendances au premier lancement (yt-dlp, Deno, ffmpeg)
- Colle un ou plusieurs liens (vidéos ou playlists), choisis le dossier, clique.
Usage perso uniquement : ne télécharge que du contenu que tu as le droit de récupérer.
"""
import os
import sys
import json
import subprocess
import threading
import queue
import traceback

APP_VERSION = "1.0.0"
RELEASES_URL = "https://github.com/QuentinIII/mediadownloadtool/releases/latest"
FROZEN = getattr(sys, "frozen", False)          # True dans l'exe PyInstaller
BUNDLE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- dépendances
DEPS = [
    ("yt_dlp", "yt-dlp[default]"),     # inclut yt-dlp-ejs (requis pour YouTube)
    ("yt_dlp_ejs", "yt-dlp-ejs"),
    ("imageio_ffmpeg", "imageio-ffmpeg"),  # ffmpeg embarqué, pas d'install manuelle
    ("deno", "deno"),                  # runtime JavaScript requis par YouTube
]


def pip_install(*pkgs, upgrade=True):
    cmd = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check"]
    if upgrade:
        cmd.append("-U")
    cmd += list(pkgs)
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        # Python système (Linux/macOS) : on retente en --user
        subprocess.check_call(cmd + ["--user"])


def ensure_deps():
    import importlib
    missing = []
    for mod, pkg in DEPS:
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        print("Installation des dépendances :", ", ".join(missing))
        pip_install(*missing)
        importlib.invalidate_caches()
        if hasattr(sys, "_clear_type_cache"):
            sys._clear_type_cache()
        # --user peut ajouter un dossier site-packages pas encore dans sys.path
        import site
        try:
            site.addsitedir(site.getusersitepackages())
        except Exception:
            pass


if not FROZEN:          # l'exe embarque déjà tout
    ensure_deps()

import yt_dlp


def _bundled(name):
    exe = name + (".exe" if sys.platform.startswith("win") else "")
    p = os.path.join(BUNDLE_DIR, "bin", exe)
    return p if os.path.isfile(p) else None


def find_ffmpeg():
    p = _bundled("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def find_deno():
    p = _bundled("deno")
    if p:
        return p
    try:
        import deno
        return deno.find_deno_bin()
    except Exception:
        return None


FFMPEG_PATH = find_ffmpeg()
DENO_PATH = find_deno()


def selftest(out_file):
    """Vérifie que tout est bien embarqué (utilisé par la CI sur l'exe)."""
    res = {"app": APP_VERSION, "frozen": FROZEN, "yt_dlp": yt_dlp.version.__version__}
    ok = True
    for key, path, arg in (("ffmpeg", FFMPEG_PATH, "-version"), ("deno", DENO_PATH, "--version")):
        try:
            out = subprocess.run([path, arg], capture_output=True, text=True, timeout=60)
            res[key] = out.stdout.splitlines()[0] if out.returncode == 0 else f"rc={out.returncode}"
            ok &= out.returncode == 0
        except Exception as e:
            res[key] = f"ERREUR: {e}"
            ok = False
    try:
        import yt_dlp_ejs
        res["yt_dlp_ejs"] = getattr(yt_dlp_ejs, "version", "ok")
    except Exception as e:
        res["yt_dlp_ejs"] = f"ERREUR: {e}"
        ok = False
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "js_runtimes": {"deno": {"path": DENO_PATH}}}) as y:
            res["extractors"] = len(list(yt_dlp.extractor.gen_extractor_classes()))
            ok &= res["extractors"] > 100
    except Exception as e:
        res["ytdl"] = f"ERREUR: {e}"
        ok = False
    try:
        import tkinter  # noqa: F401
        res["tkinter"] = "ok"
    except Exception as e:
        res["tkinter"] = f"ERREUR: {e}"
        ok = False if FROZEN else ok
    res["ok"] = bool(ok)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    sys.exit(0 if ok else 1)


if len(sys.argv) >= 3 and sys.argv[1] == "--selftest":
    selftest(sys.argv[2])

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser


# ---------------------------------------------------------------- logger yt-dlp
class QLogger:
    def __init__(self, q):
        self.q = q

    def debug(self, msg):
        if msg.startswith("[debug]"):
            return
        if "[ExtractAudio]" in msg or "[download] Destination" in msg:
            self.q.put(("log", msg))

    def info(self, msg):
        pass

    def warning(self, msg):
        self.q.put(("log", "⚠ " + msg))

    def error(self, msg):
        self.q.put(("log", "✖ " + msg))


# ---------------------------------------------------------------- appli
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Media Download Tool {APP_VERSION} — MP3 / MP4")
        self.geometry("760x580")
        self.minsize(560, 420)
        self.q = queue.Queue()
        self.worker = None
        self.cancel = threading.Event()

        default_dir = os.path.join(os.path.expanduser("~"), "Downloads", "YouTube")
        self.out_dir = tk.StringVar(value=default_dir)
        self.mode = tk.StringVar(value="MP3")
        self.quality = tk.StringVar(value="320")
        self.vres = tk.StringVar(value="Max")
        self.compat = tk.BooleanVar(value=False)
        self.playlist = tk.BooleanVar(value=True)
        self.cover = tk.BooleanVar(value=True)

        self._build_ui()
        self.after(100, self._poll)

    # ---------- UI
    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}
        f = ttk.Frame(self)
        f.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(f, text="Liens (YouTube ou autre site, un par ligne, vidéos ou playlists) :").pack(anchor="w")
        self.urls = tk.Text(f, height=6, wrap="none")
        self.urls.pack(fill="x", **pad)
        self.urls.bind("<Control-v>", self._paste)
        self.urls.bind("<Button-3>", self._paste)  # clic droit = coller

        row = ttk.Frame(f)
        row.pack(fill="x", **pad)
        ttk.Label(row, text="Dossier :").pack(side="left")
        ttk.Entry(row, textvariable=self.out_dir).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(row, text="Parcourir…", command=self._browse).pack(side="left")
        ttk.Button(row, text="Ouvrir", command=self._open_dir).pack(side="left", padx=(6, 0))

        fmt = ttk.Frame(f)
        fmt.pack(fill="x", **pad)
        ttk.Label(fmt, text="Format :").pack(side="left")
        ttk.Radiobutton(fmt, text="MP3 (audio)", value="MP3", variable=self.mode,
                        command=self._mode_changed).pack(side="left", padx=6)
        ttk.Radiobutton(fmt, text="MP4 (vidéo)", value="MP4", variable=self.mode,
                        command=self._mode_changed).pack(side="left", padx=6)

        self.opt_mp3 = ttk.Frame(f)
        ttk.Label(self.opt_mp3, text="Qualité MP3 (kbps) :").pack(side="left")
        ttk.Combobox(self.opt_mp3, textvariable=self.quality, values=["128", "192", "256", "320"],
                     width=5, state="readonly").pack(side="left", padx=6)

        self.opt_mp4 = ttk.Frame(f)
        ttk.Label(self.opt_mp4, text="Résolution max :").pack(side="left")
        ttk.Combobox(self.opt_mp4, textvariable=self.vres,
                     values=["Max", "2160p", "1440p", "1080p", "720p", "480p"],
                     width=6, state="readonly").pack(side="left", padx=6)
        ttk.Checkbutton(self.opt_mp4, text="H.264 compatible (lisible partout, souvent ≤1080p)",
                        variable=self.compat).pack(side="left", padx=10)

        opts = ttk.Frame(f)
        opts.pack(fill="x", **pad)
        self._opts_anchor = opts
        ttk.Checkbutton(opts, text="Playlists entières", variable=self.playlist).pack(side="left")
        ttk.Checkbutton(opts, text="Pochette + tags", variable=self.cover).pack(side="left", padx=10)
        self._mode_changed()

        btns = ttk.Frame(f)
        btns.pack(fill="x", **pad)
        self.btn_go = ttk.Button(btns, text="⬇  Télécharger", command=self.start)
        self.btn_go.pack(side="left")
        self.btn_stop = ttk.Button(btns, text="Stop", command=self.stop, state="disabled")
        self.btn_stop.pack(side="left", padx=6)
        ttk.Button(btns, text="Mettre à jour yt-dlp", command=self.update_ytdlp).pack(side="right")

        self.status = tk.StringVar(value="Prêt.")
        ttk.Label(f, textvariable=self.status).pack(anchor="w", **pad)
        self.bar = ttk.Progressbar(f, mode="determinate", maximum=100)
        self.bar.pack(fill="x", **pad)

        self.log = tk.Text(f, height=12, state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True, **pad)

        self._log(f"yt-dlp {yt_dlp.version.__version__} | Deno : {'OK' if DENO_PATH else 'ABSENT'} | ffmpeg : {'OK' if FFMPEG_PATH else 'ABSENT'}")

    def _mode_changed(self):
        self.opt_mp3.pack_forget()
        self.opt_mp4.pack_forget()
        frame = self.opt_mp3 if self.mode.get() == "MP3" else self.opt_mp4
        frame.pack(fill="x", padx=8, pady=4, before=self._opts_anchor)

    def _paste(self, event=None):
        try:
            txt = self.clipboard_get()
        except tk.TclError:
            return "break"
        self.urls.insert("insert", txt.strip() + "\n")
        return "break"

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.out_dir.get() or os.path.expanduser("~"))
        if d:
            self.out_dir.set(d)

    def _open_dir(self):
        d = self.out_dir.get()
        os.makedirs(d, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(d)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", d])
            else:
                subprocess.Popen(["xdg-open", d])
        except Exception as e:
            self._log(f"Impossible d'ouvrir le dossier : {e}")

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_busy(self, busy):
        self.btn_go.configure(state="disabled" if busy else "normal")
        self.btn_stop.configure(state="normal" if busy else "disabled")

    # ---------- actions
    def start(self):
        urls = [u.strip() for u in self.urls.get("1.0", "end").splitlines() if u.strip()]
        urls = [u for u in urls if u.startswith("http")]
        if not urls:
            messagebox.showwarning("Aucun lien", "Colle au moins un lien (https://…).")
            return
        out = self.out_dir.get().strip()
        try:
            os.makedirs(out, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Dossier invalide", str(e))
            return
        self.cancel.clear()
        self._set_busy(True)
        self.bar["value"] = 0
        self.worker = threading.Thread(target=self._run, args=(urls, out), daemon=True)
        self.worker.start()

    def stop(self):
        self.cancel.set()
        self.status.set("Arrêt demandé…")

    def update_ytdlp(self):
        if FROZEN:
            self._log("Version .exe : télécharge la dernière release (yt-dlp à jour) :")
            self._log(RELEASES_URL)
            webbrowser.open(RELEASES_URL)
            return

        def job():
            self.q.put(("log", "Mise à jour de yt-dlp, ejs et Deno…"))
            try:
                pip_install("yt-dlp[default]", "yt-dlp-ejs", "deno")
                self.q.put(("log", "✔ Mis à jour. Relance l'appli pour utiliser la nouvelle version."))
            except Exception as e:
                self.q.put(("log", f"✖ Échec mise à jour : {e}"))
        threading.Thread(target=job, daemon=True).start()

    # ---------- téléchargement (thread)
    def _hook(self, d):
        if self.cancel.is_set():
            raise yt_dlp.utils.DownloadCancelled("Annulé par l'utilisateur")
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes", 0)
            pct = done * 100 / total if total else 0
            name = os.path.basename(d.get("filename", ""))
            self.q.put(("progress", pct, f"Téléchargement {pct:5.1f}%  –  {name[:70]}"))
        elif d["status"] == "finished":
            msg = "Conversion en MP3…" if self.mode.get() == "MP3" else "Fusion vidéo + audio…"
            self.q.put(("progress", 100, msg))

    def _pp_hook(self, d):
        if d.get("status") == "finished" and d.get("postprocessor") == "MoveFiles":
            fp = d.get("info_dict", {}).get("filepath", "")
            if fp:
                self.q.put(("log", "✔ " + os.path.basename(fp)))

    def _video_format(self):
        res = self.vres.get()
        h = f"[height<={res[:-1]}]" if res.endswith("p") else ""
        if self.compat.get():
            # H.264 + AAC : lisible sur tous les lecteurs / TV / téléphones
            return (f"bv*{h}[vcodec^=avc1]+ba[ext=m4a]/"
                    f"b{h}[ext=mp4]/bv*{h}+ba/b{h}/bv*+ba/b")
        # Meilleure image possible (souvent VP9 ou AV1 au-delà de 1080p) + audio AAC si dispo
        return f"bv*{h}+ba[ext=m4a]/bv*{h}+ba/b{h}/bv*+ba/b"

    def _opts(self, out):
        video = self.mode.get() == "MP4"
        if video:
            # garantit un .mp4 même si YouTube ne fournit qu'un fichier .webm
            pps = [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}]
        else:
            pps = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
                    "preferredquality": self.quality.get()}]
        if self.cover.get():
            pps += [{"key": "FFmpegMetadata", "add_metadata": True},
                    {"key": "EmbedThumbnail", "already_have_thumbnail": False}]
        opts = {
            "format": self._video_format() if video else "bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": os.path.join(out, "%(title)s.%(ext)s"),
            "windowsfilenames": True,          # noms de fichiers valides partout
            "trim_file_name": 180,
            "noplaylist": not self.playlist.get(),
            "ignoreerrors": True,              # une vidéo KO ne bloque pas la suite
            "retries": 10,
            "fragment_retries": 10,
            "overwrites": False,
            "ffmpeg_location": FFMPEG_PATH,
            "postprocessors": pps,
            "writethumbnail": self.cover.get(),
            "progress_hooks": [self._hook],
            "postprocessor_hooks": [self._pp_hook],
            "logger": QLogger(self.q),
            "quiet": True,
            "no_warnings": False,
            "noprogress": True,
            "remote_components": ["ejs:github"],  # secours si ejs local trop vieux
        }
        if DENO_PATH:
            opts["js_runtimes"] = {"deno": {"path": DENO_PATH}}
        if self.cover.get():
            # convertit la miniature en jpg (requis pour l'embed mp3)
            opts["postprocessors"].insert(0, {"key": "FFmpegThumbnailsConvertor",
                                              "format": "jpg", "when": "before_dl"})
        return opts

    def _run(self, urls, out):
        ok_count = 0
        try:
            with yt_dlp.YoutubeDL(self._opts(out)) as ydl:
                for i, url in enumerate(urls, 1):
                    if self.cancel.is_set():
                        break
                    self.q.put(("log", f"[{i}/{len(urls)}] {url}"))
                    try:
                        rc = ydl.download([url])
                        if rc == 0:
                            ok_count += 1
                    except yt_dlp.utils.DownloadCancelled:
                        self.q.put(("log", "⏹ Annulé."))
                        break
                    except Exception as e:
                        self.q.put(("log", f"✖ Erreur sur ce lien : {e}"))
        except Exception:
            self.q.put(("log", "✖ Erreur inattendue :\n" + traceback.format_exc()))
        self.q.put(("done", ok_count, len(urls)))

    # ---------- boucle UI
    def _poll(self):
        try:
            while True:
                item = self.q.get_nowait()
                kind = item[0]
                if kind == "log":
                    self._log(item[1])
                elif kind == "progress":
                    self.bar["value"] = item[1]
                    self.status.set(item[2])
                elif kind == "done":
                    ok, total = item[1], item[2]
                    self.status.set(f"Terminé : {ok}/{total} lien(s) sans erreur.")
                    self.bar["value"] = 100
                    self._set_busy(False)
                    if ok < total:
                        self._log("Astuce : si YouTube bloque, clique « Mettre à jour yt-dlp » puis relance.")
        except queue.Empty:
            pass
        self.after(100, self._poll)


if __name__ == "__main__":
    try:
        App().mainloop()
    except Exception:
        err = traceback.format_exc()
        print(err)
        try:
            messagebox.showerror("Erreur", err)
        except Exception:
            pass
        input("Appuie sur Entrée pour fermer…")
