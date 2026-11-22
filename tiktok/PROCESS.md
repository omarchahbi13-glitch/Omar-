# Méthode quotidienne — DO BRAZILLL CLIPS (TikTok)

Objectif : chaque jour, monter **5 nouveaux clips** et les programmer sur TikTok via Metricool pour le **premier jour à venir
qui n'a pas encore ses 5 posts** (vérifier avec getScheduledPosts), à **09:00, 12:00, 15:00, 18:00 et 21:00 (Europe/Paris)**, en publication directe et publique.

## Chaînes Twitch (classées par vues GTA 6, mesure du 22/11/2026)
Américains : ishowspeed, kaicenat, xqc, caseoh_, jynxzi, lirik, hasanabi, summit1g
Français : squeezie, anyme023, gotaga, michou, domingo, kamet0, zerator, aminematue
(Neon streame sur Kick, inaccessible depuis l'environnement : ne pas l'utiliser.)
Refaire le classement de temps en temps : somme des vues des clips `Grand Theft Auto VI` de la semaine par chaîne.

## Ordre de priorité
1. **GTA 6 d'abord** : clips dont la catégorie (`categories` dans `yt-dlp -j`) est `Grand Theft Auto VI`.
2. Quand il n'y a plus de bon clip GTA 6 non publié : les autres clips de ces chaînes (Just Chatting, autres jeux…).
3. **Répartition (demande du propriétaire)** : beaucoup de streamers français et d'IShowSpeed, quelques autres américains. **Varier le mélange et l'ordre chaque jour** (ex. 3 FR + 1 Speed + 1 US, puis 2 FR + 2 Speed + 1 US, puis 4 FR + 1 Speed, puis 2 FR + 1 Speed + 2 US…), jamais deux jours identiques de suite. 2 clips maximum par chaîne et par jour, pas la même chaîne à deux créneaux consécutifs.
4. Les clips en anglais sont acceptés ; sous-titres en anglais.
5. **Accroche (`hook`) uniquement pour les streamers français.** Streamers non français : pas de champ `hook` du tout.
6. Ignorer toute chaîne présente dans `tiktok/chaines_bloquees.json`.

## Règles anti-blocage TikTok (obligatoires)
- **Jamais** : nudité / scène sexuelle (même dans le jeu), violence réelle, drogue, propos haineux, mineurs en danger. Dans le doute, écarter.
- Si le jeu montre une scène suggestive (ou n'est pas intéressant) mais que la réaction vaut le coup : layout `camfocus` (webcam seule agrandie) sur tout le clip.
- **IShowSpeed** : montage normal (`split`, webcam + jeu) par défaut, clip en entier. **Uniquement** si le clip montre du sexuel ou de la nudité : `camfocus` (webcam seule) sur toute la durée. Écarter si le son lui-même est explicite.
- Gros mots : toujours censurés dans les sous-titres (`fixes`, ex. f***, sh*t, p***) ; écarter un clip dont la vulgarité est le cœur.
- Toujours un vrai montage (format vertical, bande, sous-titres, coupes, zooms) : jamais le clip brut.
- Jamais deux fois le même clip (vérifier `posted.json`), jamais une vidéo déjà postée par un autre compte TikTok.
- 5 posts par jour (9 h, 12 h, 15 h, 18 h, 21 h), toujours aux mêmes heures.
- 5 hashtags maximum, pertinents ; pas de hashtags « follow4follow », « like4like » ou sans rapport.
- `isAigc: false` (vidéo réelle montée), `commercialContent*` à false.
- S'il y a moins de 5 bons clips, en programmer moins plutôt que des vidéos médiocres.

## 0. Surveillance des signalements (à faire en premier, chaque jour)
- Avec les outils d'analyse Metricool (getAnalyticsAvailableMetrics puis getAnalyticsDataByMetrics, réseau `tiktok`, connecteur `posts`),
  récupérer les vidéos TikTok publiées ces 3 derniers jours et les comparer aux publications prévues dans `posted.json`.
- Signes d'un problème : vidéo prévue introuvable 12 h après son heure, statut d'erreur dans getScheduledPosts,
  vidéo à 0 vue après 24 h, ou vues qui chutent à zéro pour toutes les vidéos d'une même chaîne.
- En cas de problème sur une chaîne : l'ajouter dans `chaines_bloquees.json` avec `"statut": "en pause - à confirmer"`, la date et la raison,
  ne plus l'utiliser, et commencer le résumé final par **« ⚠️ ALERTE »** (chaîne, vidéo, ce qui a été constaté) pour prévenir le propriétaire.
- Le propriétaire décide ensuite : arrêt définitif de la chaîne ou changement de contenu.

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
- **Ne pas couper les silences** (demande du propriétaire) : garder le clip entier, `segments: [[0, durée]]` (60 s max).
  Choisir une **accroche** (≤ 40 caractères, majuscules, streamers français uniquement) et les **zooms** sur les réactions.
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
- Texte (`text`) : `ALLEZ VOIR DANS LA BIO 🔗` + 5 hashtags (choix validé par le propriétaire) :
  - streamer **français** : `#<streamer> #<jeu> #twitchfr #fyp #pourtoi`
  - streamer **non français** : `#<streamer> #<jeu> #twitchclips #fyp #foryou`
  - `#<jeu>` = `#gta6` pour GTA VI ; **sinon pas le nom du jeu** : `#humour` (streamer français) ou `#funny` (streamer non français).
  - hashtag du streamer : #ishowspeed, #kaicenat, #xqc, #caseoh, #jynxzi, #lirik, #hasanabi, #summit1g, #squeezie, #anyme, #gotaga,
    #michou, #domingo, #kameto, #zerator, #amine.

## Mises en page de render.py
- `split` : webcam (`cam: [x,y,w,h]`) en haut, bande, jeu en bas (`game_x`).
- `camfocus` : webcam `cam` agrandie au centre sur fond flou, bande dessous ; idéal quand la webcam est petite ou le jeu à cacher.
- `cam` : source qui n'est que la webcam (`face_x`).
- `layouts` : une mise en page par segment (ex. `["split","camfocus"]`).

## 6. Ménage
Supprimer du dépôt les dossiers `tiktok/<date>/` de plus de 7 jours (Metricool garde sa propre copie dès la programmation).
