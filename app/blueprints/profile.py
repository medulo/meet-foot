"""
profile.py
----------
Le Profil : infos du compte, mes publications, Paramètres (modifier mes
infos, langue, abonnement), et la visite du profil d'un autre utilisateur.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session

from .. import database as db

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profil")
def profil():
    email = session["email"]
    type_compte = session["type_compte"]
    _, compte = db.trouver_utilisateur_par_email(email)
    mes_posts = db.lister_posts_de(email)
    return render_template("profil.html", compte=compte, type_compte=type_compte, mes_posts=mes_posts)


@profile_bp.route("/profil/publication/<int:post_id>/visibilite", methods=["POST"])
def basculer_visibilite_post(post_id):
    db.changer_visibilite_post(post_id, session["email"])
    return redirect(url_for("profile.profil"))


@profile_bp.route("/profil/parametres")
def parametres():
    return render_template("parametres.html")


@profile_bp.route("/profil/modifier", methods=["GET", "POST"])
def modifier_profil():
    email = session["email"]
    type_compte = session["type_compte"]

    if request.method == "POST":
        if type_compte == "club":
            db.modifier_club(
                email, request.form["nom_club"], request.form.get("logo_url", "").strip(),
                request.form["pays"], request.form.get("ligue", "").strip(),
            )
        else:
            db.modifier_particulier(
                email, request.form["nom"], request.form["prenoms"],
                request.form["nationalite"], request.form.get("poste", "").strip(),
            )
        return redirect(url_for("profile.profil"))

    _, compte = db.trouver_utilisateur_par_email(email)
    return render_template("modifier_profil.html", compte=compte, type_compte=type_compte)


@profile_bp.route("/profil/langue", methods=["GET", "POST"])
def langue():
    email = session["email"]
    type_compte = session["type_compte"]

    if request.method == "POST":
        db.changer_langue(type_compte, email, request.form["langue"])
        return redirect(url_for("profile.parametres"))

    _, compte = db.trouver_utilisateur_par_email(email)
    return render_template("langue.html", langue_actuelle=compte["langue"])


@profile_bp.route("/profil/abonnement", methods=["GET", "POST"])
def abonnement():
    email = session["email"]
    type_compte = session["type_compte"]

    if request.method == "POST":
        if request.form.get("action") == "resilier":
            db.resilier_abonnement(type_compte, email)
        else:
            moyen_paiement = request.form.get("moyen_paiement")
            if moyen_paiement in db.MOYENS_DE_PAIEMENT:
                db.activer_abonnement(type_compte, email, moyen_paiement)
        return redirect(url_for("profile.abonnement"))

    _, compte = db.trouver_utilisateur_par_email(email)
    return render_template(
        "abonnement.html",
        actif=db.abonnement_est_actif(type_compte, email),
        prix=db.prix_abonnement(type_compte),
        moyens=db.MOYENS_DE_PAIEMENT,
        moyen_actuel=compte["moyen_paiement"],
    )


@profile_bp.route("/profil/visite/<email_visite>")
def visiter_profil(email_visite):
    if email_visite == session["email"]:
        return redirect(url_for("profile.profil"))

    type_du_visite, compte_visite = db.trouver_utilisateur_par_email(email_visite)
    if compte_visite is None:
        return redirect(url_for("feed.accueil"))

    if not db.peut_visiter(session["type_compte"], type_du_visite):
        return render_template("acces_refuse.html", nom=db.nom_affichage(type_du_visite, compte_visite))

    posts_publics = db.lister_posts_publics_de(email_visite)
    return render_template("profil_public.html", compte=compte_visite, type_compte=type_du_visite,
                            email_visite=email_visite, posts=posts_publics)
