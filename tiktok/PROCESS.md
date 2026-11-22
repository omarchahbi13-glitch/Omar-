# Méthode quotidienne — DO BRAZILLL CLIPS (TikTok)

Objectif : chaque jour, monter **4 nouveaux clips** de Kameto (twitch.tv/kamet0) et les programmer sur TikTok via Metricool
pour le **lendemain à 12:00, 15:00, 18:00 et 21:00 (Europe/Paris)**, en publication directe et publique.

## 1. Préparer l'environnement (cloud)
```
pip install -q yt-dlp faster-whisper
cd tiktok/outils
```
Le modèle Whisper se télécharge depuis Hugging Face : lancer avec `HF_HUB_DISABLE_XET=1`.

## 2. Choisir les clips
- Lister les clips : `yt-dlp --flat-playlist --playlist-end 30 --print "%(url)s|%(title)s|%(view_count)s|%(duration)s" "https://www.twitch.tv/kamet0/clips?filter=clips&range=7d"`
  (si moins de 4 nouveaux, essayer `range=30d`).
- Ignorer tout slug déjà présent dans `tiktok/posted.json`.
- Prendre les plus vus. Écarter : musique protégée en fond, écrans de chargement / carte, sous-titres déjà incrustés, contenu choquant.
- Télécharger : `yt-dlp -f "best[height<=1080]" -o "clips/<n>.mp4" <url>` (les VOD sont réservées aux abonnés, seuls les clips sont accessibles).

## 3. Analyser chaque clip
- Audio : `ffmpeg -i clips/<n>.mp4 -ac 1 -ar 16000 clips/a<n>.wav`, puis `python3 transcribe.py` (adapter les chemins) → mots horodatés JSON.
- Extraire des images (`ffmpeg -ss T -frames:v 1`) pour repérer :
  - la **webcam** de Kameto (rectangle `cam: [x,y,w,h]` en 1920×1080 ; souvent en haut à droite vers `[1520,180,396,216]` ou `[1528,172,388,226]`),
  - l'action du jeu (`game_x`, bord gauche d'une découpe ~950 px de large),
  - ou, si l'image n'est que la webcam, `layout: "cam"` avec `face_x` (centre du visage).
- Choisir les **segments** (couper les blancs > 1,5 s, commencer sur l'action, 10 à 45 s au total),
  une **accroche** (≤ 40 caractères, majuscules) et les **zooms** (temps de sortie) sur les réactions.
- Sous-titres : supprimer (`drop_ranges`) les phrases mal transcrites plutôt que d'inventer ; censurer les insultes
  (`fixes`, ex. `{"pute":"p***"}`).

## 4. Rendre
Écrire un `job_<n>.json` (voir `jobs.json` pour des exemples) avec `"src"`, `"out":"out/<nom>.mp4"`, `"words"`, puis :
`python3 render.py job_<n>.json`
Vérifier 3-4 images de chaque rendu (sous-titres lisibles, rien ne se superpose, bande DO BRAZILLL CLIPS sous la caméra, visage non coupé).

## 5. Publier
- Copier les vidéos dans `tiktok/<AAAA-MM-JJ>/`, mettre à jour `posted.json`, commit + push sur la branche de travail.
- Lien public : `https://raw.githubusercontent.com/omarchahbi13-glitch/Omar-/<branche>/tiktok/<AAAA-MM-JJ>/<fichier>.mp4`
  (vérifier le code 200 avec curl avant de programmer).
- Metricool `createScheduledPost` : blogId `8290985`, provider `tiktok`, `autoPublish: true`, timezone `Europe/Paris`,
  `tiktokData.title` obligatoire, `privacyOption: PUBLIC_TO_EVERYONE`.
- Titre (`tiktokData.title`) : `ALLEZ VOIR DANS LA BIO` (toujours, demande du propriétaire du compte).
- Texte (`text`) : `ALLEZ VOIR DANS LA BIO 🔗` puis 5 hashtags, dans cet ordre :
  `#kameto` + 1 hashtag de contenu + `#twitchfr #fyp #pourtoi`.
  Hashtag de contenu selon le clip : `#gta6` (GTA / RP), `#jumpscare` (peur, jeu d'horreur), `#karminecorp` (webcam, discussion, esport),
  sinon le nom du jeu en un mot (ex. `#fortnite`, `#valorant`, `#minecraft`).

## 6. Ménage
Supprimer du dépôt les dossiers `tiktok/<date>/` de plus de 7 jours (Metricool garde sa propre copie dès la programmation).
