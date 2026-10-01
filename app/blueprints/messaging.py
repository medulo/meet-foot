"""
messaging.py
------------
La Messagerie : liste des conversations, démarrage d'une nouvelle
conversation, envoi de messages texte et vocaux.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session

from .. import database as db
from ..helpers import enregistrer_audio_base64

messaging_bp = Blueprint("messaging", __name__)


@messaging_bp.route("/messagerie")
def messagerie():
    conversations = db.lister_conversations(session["email"])
    return render_template("messagerie.html", conversations=conversations)


@messaging_bp.route("/messagerie/nouvelle")
def nouvelle_conversation():
    contacts = db.lister_contacts_possibles(session["email"], session["type_compte"])
    return render_template("nouvelle_conversation.html", contacts=contacts)


@messaging_bp.route("/messagerie/<autre_email>", methods=["GET", "POST"])
def conversation(autre_email):
    mon_email = session["email"]
    mon_type = session["type_compte"]

    _, mon_compte = db.trouver_utilisateur_par_email(mon_email)
    mon_nom = db.nom_affichage(mon_type, mon_compte)

    type_autre, autre_compte = db.trouver_utilisateur_par_email(autre_email)
    if autre_compte is None:
        return redirect(url_for("messaging.messagerie"))
    autre_nom = db.nom_affichage(type_autre, autre_compte)

    if request.method == "POST":
        contenu_texte = request.form.get("contenu_texte", "").strip()
        audio_base64 = request.form.get("audio_base64", "").strip()

        if contenu_texte:
            db.envoyer_message(mon_email, mon_nom, autre_email, autre_nom, "texte", contenu_texte)
        elif audio_base64:
            nom_fichier = enregistrer_audio_base64(audio_base64)
            db.envoyer_message(mon_email, mon_nom, autre_email, autre_nom, "vocal", nom_fichier)

        if contenu_texte or audio_base64:
            db.creer_notification(
                destinataire_email=autre_email,
                type_notification="message",
                texte=f"{mon_nom} vous a envoyé un message.",
                lien=url_for("messaging.conversation", autre_email=mon_email),
            )

        return redirect(url_for("messaging.conversation", autre_email=autre_email))

    messages = db.lister_messages(mon_email, autre_email)
    return render_template("conversation.html", messages=messages, mon_email=mon_email,
                            autre_email=autre_email, autre_nom=autre_nom, type_autre=type_autre)
