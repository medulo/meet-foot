"""
app/__init__.py
----------------
Le point d'entrée de l'application : c'est ici que Flask est configuré et
que les différentes parties du site (les "blueprints") sont assemblées.

Ce modèle s'appelle une "application factory" (fabrique d'application) :
au lieu de créer l'objet Flask directement dans un script, on écrit une
fonction `create_app()` qui le construit et le renvoie. C'est l'organisation
standard des projets Flask professionnels : elle permet par exemple de
créer plusieurs instances de l'appli avec des réglages différents pour les
tests, sans rien dupliquer.
"""

import os

from flask import Flask, redirect, request, session, url_for

from . import database as db


# Endpoints accessibles SANS être connecté ni abonné (inscription, connexion,
# page de paiement elle-même, fichiers statiques comme les images).
ENDPOINTS_PUBLICS = {
    "auth.index", "auth.inscription_club", "auth.inscription_particulier",
    "auth.login", "auth.logout", "static",
}
# Accessible en étant connecté, même SANS abonnement actif (c'est la page
# où l'on va justement payer).
ENDPOINTS_SANS_ABONNEMENT = ENDPOINTS_PUBLICS | {"profile.abonnement"}


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("MEETFOOT_SECRET_KEY", "cle-secrete-de-developpement-a-changer")

    # Dossiers où sont enregistrés les fichiers envoyés par les utilisateurs.
    app.config["DOSSIER_UPLOADS"] = os.path.join(app.static_folder, "uploads")
    app.config["DOSSIER_AUDIO"] = os.path.join(app.static_folder, "audio")
    os.makedirs(app.config["DOSSIER_UPLOADS"], exist_ok=True)
    os.makedirs(app.config["DOSSIER_AUDIO"], exist_ok=True)

    db.init_db()

    # --- Enregistrement des blueprints : chaque grande fonctionnalité de
    # l'appli vit dans son propre fichier sous app/blueprints/. ---
    from .blueprints.auth import auth_bp
    from .blueprints.feed import feed_bp
    from .blueprints.messaging import messaging_bp
    from .blueprints.market import market_bp
    from .blueprints.profile import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(messaging_bp)
    app.register_blueprint(market_bp)
    app.register_blueprint(profile_bp)

    # -----------------------------------------------------------------
    # Sécurité centralisée : plutôt que de répéter la même vérification
    # dans chaque route (comme dans une version débutante), on la fait
    # UNE SEULE FOIS ici, avant chaque requête, pour tout le site.
    # -----------------------------------------------------------------
    @app.before_request
    def controle_acces():
        endpoint = request.endpoint
        if endpoint is None or endpoint in ENDPOINTS_PUBLICS:
            return None

        if "email" not in session:
            return redirect(url_for("auth.login"))

        if endpoint in ENDPOINTS_SANS_ABONNEMENT:
            return None

        if not db.abonnement_est_actif(session["type_compte"], session["email"]):
            return redirect(url_for("profile.abonnement"))

        return None

    # Variables disponibles automatiquement dans TOUS les templates
    # (évite de les repasser à chaque render_template).
    @app.context_processor
    def injecter_variables_globales():
        if "email" not in session:
            return {"nb_notifs_non_lues": 0, "abonnement_ok": False}
        type_compte = session["type_compte"]
        email = session["email"]
        return {
            "nb_notifs_non_lues": db.compter_notifications_non_lues(email),
            "abonnement_ok": db.abonnement_est_actif(type_compte, email),
        }

    return app
