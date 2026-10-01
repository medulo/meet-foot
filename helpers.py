"""
helpers.py
----------
Petites fonctions réutilisées par plusieurs blueprints (enregistrement de
fichiers envoyés par l'utilisateur : photos, vidéos, messages vocaux).
"""

import base64
import os
import uuid

from flask import current_app

EXTENSIONS_VIDEO = {"mp4", "mov", "webm", "avi"}


def _extension(nom_fichier):
    if "." not in nom_fichier:
        return ""
    return nom_fichier.rsplit(".", 1)[1].lower()


def enregistrer_media(fichier):
    """
    Enregistre une photo ou une vidéo envoyée via un <input type="file">.
    Renvoie un tuple (nom_fichier_enregistre, type_media) où type_media
    vaut "image" ou "video", ou (None, None) si aucun fichier n'a été envoyé.
    """
    if fichier is None or fichier.filename == "":
        return None, None

    extension = _extension(fichier.filename)
    type_media = "video" if extension in EXTENSIONS_VIDEO else "image"

    nom_fichier = f"{uuid.uuid4().hex}.{extension}" if extension else uuid.uuid4().hex
    chemin = os.path.join(current_app.config["DOSSIER_UPLOADS"], nom_fichier)
    fichier.save(chemin)

    return nom_fichier, type_media


def enregistrer_photo(fichier):
    """Enregistre une simple photo (Market, etc.). Renvoie le nom de fichier ou None."""
    nom_fichier, _ = enregistrer_media(fichier)
    return nom_fichier


def enregistrer_audio_base64(audio_base64):
    """
    Décode un enregistrement vocal envoyé en base64 par le microphone du
    navigateur (voir static/js/messagerie.js) et l'enregistre comme fichier
    .webm. Renvoie le nom du fichier créé.
    """
    donnees_audio = base64.b64decode(audio_base64.split(",")[1])
    nom_fichier = f"{uuid.uuid4().hex}.webm"
    chemin = os.path.join(current_app.config["DOSSIER_AUDIO"], nom_fichier)
    with open(chemin, "wb") as fichier:
        fichier.write(donnees_audio)
    return nom_fichier
