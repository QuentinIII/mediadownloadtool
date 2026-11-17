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

## Installation

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

## Usage

Outil destiné à un usage personnel. Ne télécharge que du contenu que tu as le droit de récupérer (tes propres vidéos, contenus libres de droits, etc.) et respecte les conditions d'utilisation des sites.
