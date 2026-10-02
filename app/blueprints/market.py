"""
market.py
---------
Le Market (mercato) : les Clubs mettent des joueurs en vente, les Agents et
Coachs publient leur profil et ce qu'ils recherchent. Les Joueurs peuvent
consulter mais pas publier.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session

from .. import database as db
from ..helpers import enregistrer_photo

market_bp = Blueprint("market", __name__)


@market_bp.route("/market")
def market():
    email = session["email"]
    type_compte = session["type_compte"]
    _, utilisateur = db.trouver_utilisateur_par_email(email)

    annonces = db.lister_annonces_market()
    peut_publier = db.peut_publier_sur_market(type_compte, utilisateur)

    return render_template("market.html", annonces=annonces, peut_publier=peut_publier,
                            mon_email=email)


@market_bp.route("/market/publier", methods=["GET", "POST"])
def market_publier():
    email = session["email"]
    type_compte = session["type_compte"]
    _, utilisateur = db.trouver_utilisateur_par_email(email)

    if not db.peut_publier_sur_market(type_compte, utilisateur):
        return redirect(url_for("market.market"))

    if request.method == "POST":
        auteur_nom = db.nom_affichage(type_compte, utilisateur)
        photo_fichier = enregistrer_photo(request.files.get("photo"))

        if type_compte == "club":
            db.creer_annonce_joueur(
                auteur_email=email, auteur_nom=auteur_nom, logo_url=utilisateur["logo_url"],
                photo_joueur=photo_fichier, nom_joueur=request.form["nom_joueur"],
                poste=request.form["poste"], age=request.form["age"],
                prix=request.form.get("prix", "").strip(),
            )
        else:
            db.creer_annonce_recherche(
                auteur_email=email, auteur_nom=auteur_nom, photo=photo_fichier,
                texte_recherche=request.form["texte_recherche"],
            )
        return redirect(url_for("market.market"))

    return render_template("market_publier.html", type_compte=type_compte)
