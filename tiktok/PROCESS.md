# Méthode quotidienne — DO BRAZILLL CLIPS (TikTok)

Objectif : chaque jour, monter **4 nouveaux clips** et les programmer sur TikTok via Metricool pour le **premier jour à venir
qui n'a pas encore ses 4 posts** (vérifier avec getScheduledPosts), à **12:00, 15:00, 18:00 et 21:00 (Europe/Paris)**, en publication directe et publique.

## Chaînes Twitch (toutes)
| Chaîne Twitch | Hashtag streamer | Hashtag communauté |
|---|---|---|
| ishowspeed | #ishowspeed | #twitch |
| kaicenat | #kaicenat | #twitch |
| aminematue | #amine | #twitchfr |
| anyme023 | #anyme | #twitchfr |
| squeezie | #squeezie | #twitchfr |
| michou | #michou | #twitchfr |
| domingo | #domingo | #twitchfr |
| kamet0 | #kameto | #twitchfr |

## Ordre de priorité
1. **GTA 6 d'abord** : clips dont la catégorie (`categories` dans `yt-dlp -j`) est `Grand Theft Auto VI`.
2. Quand il n'y a plus de bon clip GTA 6 non publié : les autres clips de ces chaînes (Just Chatting, autres jeux…).
3. Varier : **2 clips maximum par chaîne et par jour**, et ne pas mettre la même chaîne à deux créneaux consécutifs.
4. Les clips en anglais (Speed, Kai Cenat) sont acceptés ; sous-titres en anglais, accroche en français.

## Règles anti-blocage TikTok (obligatoires)
- **Jamais** : nudité / scène sexuelle (même dans le jeu), violence réelle, drogue, propos haineux, mineurs en danger. Dans le doute, écarter.
- Gros mots : toujours censurés dans les sous-titres (`fixes`, ex. f***, sh*t, p***) ; écarter un clip dont la vulgarité est le cœur.
- Toujours un vrai montage (format vertical, bande, sous-titres, coupes, zooms) : jamais le clip brut.
- Jamais deux fois le même clip (vérifier `posted.json`), jamais une vidéo déjà postée par un autre compte TikTok.
- 4 posts par jour maximum, espacés de 3 h, toujours aux mêmes heures.
- 5 hashtags maximum, pertinents ; pas de hashtags « follow4follow », « like4like » ou sans rapport.
- `isAigc: false` (vidéo réelle montée), `commercialContent*` à false.
- S'il y a moins de 4 bons clips, en programmer moins plutôt que des vidéos médiocres.

## 1. Préparer l'environnement (cloud)
```
pip install -q yt-dlp faster-whisper
cd tiktok/outils
```
Le modèle Whisper se télécharge depuis Hugging Face : lancer avec `HF_HUB_DISABLE_XET=1`.

## 2. Choisir les clips
- Lister les clips de chaque chaîne avec leur jeu :
  `yt-dlp -j --skip-download --playlist-end 15 "https://www.twitch.tv/<chaine>/clips?filter=clips&range=7d"`
  (champs utiles : `categories`, `view_count`, `duration`, `title`, `webpage_url` ; si trop peu, `range=30d`).
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
  hashtag du streamer + hashtag du jeu + hashtag communauté + `#fyp #pourtoi` (voir le tableau des chaînes).
  Hashtag du jeu : `#gta6` pour GTA VI, sinon le nom du jeu en un mot (ex. `#robrun`, `#fortnite`), ou `#humour` pour Just Chatting.

## 6. Ménage
Supprimer du dépôt les dossiers `tiktok/<date>/` de plus de 7 jours (Metricool garde sa propre copie dès la programmation).
