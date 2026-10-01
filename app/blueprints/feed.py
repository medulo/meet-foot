"""
feed.py
-------
Le fil d'actualité (Accueil), les Notifications, et la publication de
contenu (Créer) : photo, vidéo ou texte, public ou privé.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session

from .. import database as db
from ..helpers import enregistrer_media

feed_bp = Blueprint("feed", __name__)


@feed_bp.route("/accueil")
def accueil():
    email = session["email"]
    posts = db.lister_posts(email)
    return render_template("accueil.html", posts=posts)


@feed_bp.route("/publication/<int:post_id>/jaime", methods=["POST"])
def like(post_id):
    email = session["email"]
    action = db.toggle_like(post_id, email)

    if action == "ajout":
        post = db.recuperer_post(post_id)
        if post is not None and post["auteur_email"] != email:
            _, utilisateur = db.trouver_utilisateur_par_email(email)
            nom_utilisateur = db.nom_affichage(session["type_compte"], utilisateur)
            db.creer_notification(
                destinataire_email=post["auteur_email"],
                type_notification="like",
                texte=f"{nom_utilisateur} a aimé votre publication.",
                lien=url_for("feed.accueil"),
            )

    return redirect(url_for("feed.accueil"))


@feed_bp.route("/notifications")
def notifications():
    email = session["email"]
    liste = db.lister_notifications(email)
    db.marquer_notifications_lues(email)
    return render_template("notifications.html", notifications=liste)


@feed_bp.route("/creer", methods=["GET", "POST"])
def creer():
    if request.method == "POST":
        email = session["email"]
        type_compte = session["type_compte"]
        _, utilisateur = db.trouver_utilisateur_par_email(email)
        auteur_nom = db.nom_affichage(type_compte, utilisateur)

        contenu_texte = request.form.get("contenu_texte", "").strip()
        visibilite = request.form.get("visibilite", "public")
        if visibilite not in ("public", "prive"):
            visibilite = "public"

        fichier_media, type_media = enregistrer_media(request.files.get("media"))

        if contenu_texte or fichier_media:
            db.creer_post(type_compte, email, auteur_nom, contenu_texte, None,
                           fichier_media=fichier_media, type_media=type_media,
                           visibilite=visibilite)
            return redirect(url_for("feed.accueil"))

    return render_template("creer.html")
