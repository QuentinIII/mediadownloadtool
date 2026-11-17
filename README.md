# mediadownloadtool

A tool to download almost any songs and videos on the internet.

Petite appli graphique (Python + Tkinter) basée sur [yt-dlp](https://github.com/yt-dlp/yt-dlp) : tu colles des liens, tu choisis **MP3** ou **MP4**, tu cliques.

## Fonctionnalités

- **MP3** : 128 / 192 / 256 / 320 kbps
- **MP4** : résolution max (4K / 8K / 60 fps si dispo) ou plafonnée (2160p → 480p)
  - option **H.264 compatible** pour un fichier lisible partout (souvent ≤ 1080p)
- Plusieurs liens d'un coup, playlists entières (désactivable)
- Pochette + tags intégrés au fichier
- Barre de progression, bouton Stop, log
- Une vidéo en erreur ne bloque pas les suivantes
- Bouton **Mettre à jour yt-dlp** (à utiliser quand YouTube casse quelque chose)
- **Zéro install manuelle** : au premier lancement, l'appli installe yt-dlp, ffmpeg (via `imageio-ffmpeg`) et Deno (le runtime JavaScript requis par YouTube depuis yt-dlp 2025.11)

## Version portable (.exe Windows) — le plus simple

1. Aller dans [**Releases**](https://github.com/QuentinIII/mediadownloadtool/releases/latest)
2. Télécharger `mediadownloadtool-vX.Y.Z-windows-x64.exe`
3. Double-clic. C'est tout : pas de Python, pas d'installation, ffmpeg et Deno sont inclus.

> Windows SmartScreen peut afficher « Windows a protégé votre ordinateur » (exe non signé) → **Informations complémentaires** → **Exécuter quand même**.
> Le premier démarrage prend quelques secondes (l'exe se décompresse).
> Si YouTube casse un jour, télécharger la dernière release (le bouton « Mettre à jour » ouvre la page).

## Installation depuis le code source

1. Installer **Python 3.10+** depuis [python.org](https://www.python.org/downloads/) (Windows : cocher **« Add Python to PATH »**).
2. Télécharger ce dépôt (`Code` → `Download ZIP`) ou :
   ```bash
   git clone https://github.com/QuentinIII/mediadownloadtool.git
   ```
3. Lancer :
   - **Windows** : double-clic sur `Lancer.bat`
   - **Linux / macOS** : `./lancer.sh` (sous Linux, installer Tkinter si besoin : `sudo apt install python3-tk`)

Le premier lancement prend ~1 minute (installation des dépendances). Installation manuelle possible :

```bash
pip install -r requirements.txt
python mediadownloadtool.py
```

Dossier de sortie par défaut : `~/Downloads/YouTube` (modifiable dans l'appli).

## À propos du MP4 en résolution max

Au-delà de 1080p, YouTube encode quasiment tout en **AV1** ou **VP9**. Le `.mp4` obtenu est bien en qualité max et se lit dans VLC, les navigateurs, DaVinci Resolve récent… mais certains lecteurs (vieilles TV, lecteur Windows sans extension AV1, Premiere) peuvent le refuser. Dans ce cas, cocher **H.264 compatible**.

## Dépannage

| Problème | Solution |
|---|---|
| Une vidéo YouTube échoue / « Sign in to confirm » / formats manquants | Bouton **Mettre à jour yt-dlp**, puis relancer l'appli |
| `Deno : ABSENT` dans le log | `pip install -U deno` puis relancer |
| `No module named tkinter` (Linux) | `sudo apt install python3-tk` |
| Le `.bat` se ferme tout de suite | Python n'est pas dans le PATH → réinstaller Python en cochant « Add Python to PATH » |

## Construire l'exe soi-même

Automatique : GitHub Actions (`.github/workflows/build-exe.yml`) construit l'exe sur Windows, le teste (`--selftest`) et le publie :

```bash
git tag v1.0.1
git push origin v1.0.1      # -> nouvelle Release avec l'exe
```

Ou depuis GitHub : **Actions → Build portable exe → Run workflow**
- champ *version* rempli (ex. `1.0.0`) → Release publiée avec l'exe
- champ vide → exe dispo en artefact du run, sans release

En local (sous Windows) :

```bash
pip install -r requirements.txt pyinstaller
python build.py             # -> dist/mediadownloadtool.exe
```

## Licence

Code sous licence [MIT](LICENSE).
L'exe embarque des composants tiers sous leur propre licence : [yt-dlp](https://github.com/yt-dlp/yt-dlp) (Unlicense), [FFmpeg](https://ffmpeg.org/legal.html) (LGPL/GPL, binaire fourni par [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg)), [Deno](https://github.com/denoland/deno) (MIT).

## Usage

Outil destiné à un usage personnel. Ne télécharge que du contenu que tu as le droit de récupérer (tes propres vidéos, contenus libres de droits, etc.) et respecte les conditions d'utilisation des sites.
