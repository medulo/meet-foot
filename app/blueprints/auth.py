"""
auth.py
-------
Tout ce qui concerne l'identité : page d'accueil publique, inscription
(Club / Particulier), connexion, déconnexion.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

from .. import database as db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if "email" in session:
        return redirect(url_for("feed.accueil"))
    return render_template("index.html")


@auth_bp.route("/inscription/club", methods=["GET", "POST"])
def inscription_club():
    erreur = None
    if request.method == "POST":
        nom_club = request.form["nom_club"]
        logo_url = request.form.get("logo_url", "").strip()
        discipline = request.form["discipline"]
        pays = request.form["pays"]
        ligue = request.form.get("ligue", "").strip()
        email = request.form["email"].strip().lower()
        mot_de_passe = request.form["mot_de_passe"]

        _, existant = db.trouver_utilisateur_par_email(email)
        if existant is not None:
            erreur = "Un compte existe déjà avec cet email."
        else:
            mot_de_passe_hache = generate_password_hash(mot_de_passe)
            db.creer_club(nom_club, logo_url, discipline, pays, ligue, email, mot_de_passe_hache)
            session["email"] = email
            session["type_compte"] = "club"
            return redirect(url_for("profile.abonnement"))

    return render_template("inscription_club.html", erreur=erreur)


@auth_bp.route("/inscription/particulier", methods=["GET", "POST"])
def inscription_particulier():
    erreur = None
    if request.method == "POST":
        nom = request.form["nom"]
        prenoms = request.form["prenoms"]
        date_naissance = request.form["date_naissance"]
        nationalite = request.form["nationalite"]
        profession = request.form["profession"]
        sport = request.form["sport"]
        poste = request.form.get("poste", "").strip() if profession == "Joueur" else ""
        email = request.form["email"].strip().lower()
        mot_de_passe = request.form["mot_de_passe"]

        _, existant = db.trouver_utilisateur_par_email(email)
        if existant is not None:
            erreur = "Un compte existe déjà avec cet email."
        else:
            mot_de_passe_hache = generate_password_hash(mot_de_passe)
            db.creer_particulier(nom, prenoms, date_naissance, nationalite,
                                  profession, sport, poste, email, mot_de_passe_hache)
            session["email"] = email
            session["type_compte"] = "particulier"
            return redirect(url_for("profile.abonnement"))

    return render_template("inscription_particulier.html", erreur=erreur)


@auth_bp.route("/connexion", methods=["GET", "POST"])
def login():
    erreur = None
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        mot_de_passe = request.form["mot_de_passe"]

        type_compte, utilisateur = db.trouver_utilisateur_par_email(email)

        if utilisateur is not None and check_password_hash(utilisateur["mot_de_passe"], mot_de_passe):
            session["email"] = email
            session["type_compte"] = type_compte
            return redirect(url_for("feed.accueil"))
        erreur = "Email ou mot de passe incorrect."

    return render_template("login.html", erreur=erreur)


@auth_bp.route("/deconnexion")
def logout():
    session.clear()
    return redirect(url_for("auth.index"))
