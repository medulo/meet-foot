"""
database.py
------------
Toute la logique de base de données de Meet Foot (SQLite).

Organisation de ce fichier (repère-toi avec les commentaires de section) :
    1. Connexion et création des tables
    2. Comptes (Club / Particulier)
    3. Publications (posts) et likes
    4. Messagerie
    5. Notifications
    6. Profil, abonnement, visite de profil
    7. Market

Vocabulaire :
- une fonction est déclarée avec `def`
- `self` n'apparaît pas ici : on n'utilise pas de classes, seulement des
  fonctions qui ouvrent une connexion, font leur travail, puis la referment
- `?` dans une requête SQL est un "trou" rempli ensuite par les valeurs
  passées en paramètre (ça protège contre les injections SQL)
"""

import sqlite3
from datetime import datetime

DB_NAME = "meetfoot.db"


# ---------------------------------------------------------------------------
# 1. CONNEXION ET CRÉATION DES TABLES
# ---------------------------------------------------------------------------
def get_connection():
    """Ouvre une connexion vers le fichier de base de données."""
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def ajouter_colonne_si_absente(table, colonne, type_sql):
    """
    Ajoute une colonne à une table existante si elle n'existe pas déjà.
    Utile pour faire évoluer la base sans perdre les données déjà créées.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    colonnes_existantes = [ligne["name"] for ligne in cursor.fetchall()]
    if colonne not in colonnes_existantes:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {colonne} {type_sql}")
        connection.commit()
    connection.close()


def init_db():
    """Crée toutes les tables si elles n'existent pas encore, et applique
    les migrations (nouvelles colonnes) sur les tables déjà existantes."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clubs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_club TEXT NOT NULL,
            logo_url TEXT,
            discipline TEXT NOT NULL,
            pays TEXT NOT NULL,
            ligue TEXT,
            email TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS particuliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenoms TEXT NOT NULL,
            date_naissance TEXT NOT NULL,
            nationalite TEXT NOT NULL,
            profession TEXT NOT NULL,
            sport TEXT NOT NULL,
            poste TEXT,
            email TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auteur_type TEXT NOT NULL,
            auteur_email TEXT NOT NULL,
            auteur_nom TEXT NOT NULL,
            contenu_texte TEXT,
            image_url TEXT,
            date_publication TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            email_utilisateur TEXT NOT NULL,
            UNIQUE(post_id, email_utilisateur)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expediteur_email TEXT NOT NULL,
            expediteur_nom TEXT NOT NULL,
            destinataire_email TEXT NOT NULL,
            destinataire_nom TEXT NOT NULL,
            type_message TEXT NOT NULL,
            contenu TEXT NOT NULL,
            date_envoi TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destinataire_email TEXT NOT NULL,
            type_notification TEXT NOT NULL,
            texte TEXT NOT NULL,
            lien TEXT NOT NULL,
            date_notification TEXT NOT NULL,
            lue INTEGER NOT NULL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_annonce TEXT NOT NULL,
            auteur_type TEXT NOT NULL,
            auteur_email TEXT NOT NULL,
            auteur_nom TEXT NOT NULL,
            logo_url TEXT,
            photo_url TEXT,
            nom_joueur TEXT,
            poste TEXT,
            age INTEGER,
            prix TEXT,
            description TEXT,
            date_publication TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()

    # --- Migrations : colonnes ajoutées après la première version ---
    ajouter_colonne_si_absente("posts", "fichier_media", "TEXT")
    ajouter_colonne_si_absente("posts", "type_media", "TEXT")
    ajouter_colonne_si_absente("posts", "visibilite", "TEXT NOT NULL DEFAULT 'public'")

    ajouter_colonne_si_absente("clubs", "langue", "TEXT NOT NULL DEFAULT 'Français'")
    ajouter_colonne_si_absente("particuliers", "langue", "TEXT NOT NULL DEFAULT 'Français'")

    # L'application est payante : chaque compte doit régler un abonnement
    # mensuel (Wave / Moov Money / MTN Money) pour utiliser l'appli.
    ajouter_colonne_si_absente("clubs", "abonnement_actif", "INTEGER NOT NULL DEFAULT 0")
    ajouter_colonne_si_absente("clubs", "moyen_paiement", "TEXT")
    ajouter_colonne_si_absente("particuliers", "abonnement_actif", "INTEGER NOT NULL DEFAULT 0")
    ajouter_colonne_si_absente("particuliers", "moyen_paiement", "TEXT")


# ---------------------------------------------------------------------------
# 2. COMPTES (CLUB / PARTICULIER)
# ---------------------------------------------------------------------------
def creer_club(nom_club, logo_url, discipline, pays, ligue, email, mot_de_passe):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO clubs (nom_club, logo_url, discipline, pays, ligue, email, mot_de_passe)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (nom_club, logo_url, discipline, pays, ligue, email, mot_de_passe))
    connection.commit()
    connection.close()


def creer_particulier(nom, prenoms, date_naissance, nationalite, profession,
                       sport, poste, email, mot_de_passe):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO particuliers
            (nom, prenoms, date_naissance, nationalite, profession, sport, poste, email, mot_de_passe)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nom, prenoms, date_naissance, nationalite, profession, sport, poste, email, mot_de_passe))
    connection.commit()
    connection.close()


def trouver_utilisateur_par_email(email):
    """Renvoie (type_de_compte, ligne) où type_de_compte vaut "club" ou
    "particulier", ou (None, None) si l'email n'est associé à aucun compte."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM clubs WHERE email = ?", (email,))
    club = cursor.fetchone()
    if club is not None:
        connection.close()
        return "club", club

    cursor.execute("SELECT * FROM particuliers WHERE email = ?", (email,))
    particulier = cursor.fetchone()
    connection.close()
    if particulier is not None:
        return "particulier", particulier

    return None, None


def nom_affichage(type_compte, utilisateur):
    """Nom "prêt à afficher" : nom du club, ou "Prénoms Nom" pour un particulier."""
    if type_compte == "club":
        return utilisateur["nom_club"]
    return f"{utilisateur['prenoms']} {utilisateur['nom']}"

# ---------------------------------------------------------------------------
# 3. PUBLICATIONS (POSTS) ET LIKES
# ---------------------------------------------------------------------------
def creer_post(auteur_type, auteur_email, auteur_nom, contenu_texte, image_url,
                fichier_media=None, type_media=None, visibilite="public"):
    connection = get_connection()
    cursor = connection.cursor()
    date_publication = datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute("""
        INSERT INTO posts (auteur_type, auteur_email, auteur_nom, contenu_texte,
                            image_url, fichier_media, type_media, visibilite, date_publication)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (auteur_type, auteur_email, auteur_nom, contenu_texte, image_url,
          fichier_media, type_media, visibilite, date_publication))
    connection.commit()
    connection.close()


def lister_posts(email_utilisateur_courant):
    """Fil d'actualité : tous les posts publics, + les posts privés de
    l'utilisateur courant lui-même, du plus récent au plus ancien."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT * FROM posts
        WHERE visibilite = 'public' OR auteur_email = ?
        ORDER BY id DESC
    """, (email_utilisateur_courant,))
    posts_bruts = cursor.fetchall()

    posts = []
    for post in posts_bruts:
        cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = ?", (post["id"],))
        nombre_likes = cursor.fetchone()[0]
        cursor.execute(
            "SELECT 1 FROM likes WHERE post_id = ? AND email_utilisateur = ?",
            (post["id"], email_utilisateur_courant)
        )
        deja_like = cursor.fetchone() is not None

        post_dict = dict(post)
        post_dict["nombre_likes"] = nombre_likes
        post_dict["deja_like"] = deja_like
        posts.append(post_dict)

    connection.close()
    return posts


def recuperer_post(post_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    connection.close()
    return post


def toggle_like(post_id, email_utilisateur):
    """Ajoute/retire un like. Renvoie "ajout" ou "suppression"."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id FROM likes WHERE post_id = ? AND email_utilisateur = ?",
        (post_id, email_utilisateur)
    )
    like_existant = cursor.fetchone()

    if like_existant is not None:
        cursor.execute("DELETE FROM likes WHERE id = ?", (like_existant["id"],))
        action = "suppression"
    else:
        cursor.execute(
            "INSERT INTO likes (post_id, email_utilisateur) VALUES (?, ?)",
            (post_id, email_utilisateur)
        )
        action = "ajout"

    connection.commit()
    connection.close()
    return action


# ---------------------------------------------------------------------------
# 4. MESSAGERIE
# ---------------------------------------------------------------------------
def envoyer_message(expediteur_email, expediteur_nom, destinataire_email,
                     destinataire_nom, type_message, contenu):
    connection = get_connection()
    cursor = connection.cursor()
    date_envoi = datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute("""
        INSERT INTO messages
            (expediteur_email, expediteur_nom, destinataire_email, destinataire_nom,
             type_message, contenu, date_envoi)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (expediteur_email, expediteur_nom, destinataire_email, destinataire_nom,
          type_message, contenu, date_envoi))
    connection.commit()
    connection.close()


def lister_conversations(email):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT * FROM messages
        WHERE expediteur_email = ? OR destinataire_email = ?
        ORDER BY id DESC
    """, (email, email))
    tous_les_messages = cursor.fetchall()
    connection.close()

    conversations = {}
    for message in tous_les_messages:
        if message["expediteur_email"] == email:
            autre_email = message["destinataire_email"]
            autre_nom = message["destinataire_nom"]
        else:
            autre_email = message["expediteur_email"]
            autre_nom = message["expediteur_nom"]

        if autre_email not in conversations:
            apercu = "Message vocal" if message["type_message"] == "vocal" else message["contenu"]
            conversations[autre_email] = {
                "email": autre_email,
                "nom": autre_nom,
                "dernier_message": apercu,
                "date": message["date_envoi"],
            }

    return list(conversations.values())


def lister_messages(email_a, email_b):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT * FROM messages
        WHERE (expediteur_email = ? AND destinataire_email = ?)
           OR (expediteur_email = ? AND destinataire_email = ?)
        ORDER BY id ASC
    """, (email_a, email_b, email_b, email_a))
    messages = cursor.fetchall()
    connection.close()
    return messages


def lister_contacts_possibles(email_courant, type_courant):
    """Contacts avec qui démarrer une conversation : un Club peut contacter
    tout le monde, un Particulier uniquement les Clubs."""
    connection = get_connection()
    cursor = connection.cursor()
    contacts = []

    cursor.execute("SELECT nom_club AS nom, email FROM clubs WHERE email != ?", (email_courant,))
    for club in cursor.fetchall():
        contacts.append({"email": club["email"], "nom": club["nom"], "type": "club"})

    if type_courant == "club":
        cursor.execute("SELECT nom, prenoms, email FROM particuliers WHERE email != ?", (email_courant,))
        for particulier in cursor.fetchall():
            nom_complet = f"{particulier['prenoms']} {particulier['nom']}"
            contacts.append({"email": particulier["email"], "nom": nom_complet, "type": "particulier"})

    connection.close()
    return contacts


# ---------------------------------------------------------------------------
# 5. NOTIFICATIONS
# ---------------------------------------------------------------------------
def creer_notification(destinataire_email, type_notification, texte, lien):
    connection = get_connection()
    cursor = connection.cursor()
    date_notification = datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute("""
        INSERT INTO notifications (destinataire_email, type_notification, texte, lien, date_notification)
        VALUES (?, ?, ?, ?, ?)
    """, (destinataire_email, type_notification, texte, lien, date_notification))
    connection.commit()
    connection.close()


def lister_notifications(email):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM notifications WHERE destinataire_email = ? ORDER BY id DESC", (email,)
    )
    notifications = cursor.fetchall()
    connection.close()
    return notifications


def compter_notifications_non_lues(email):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM notifications WHERE destinataire_email = ? AND lue = 0", (email,)
    )
    nombre = cursor.fetchone()[0]
    connection.close()
    return nombre


def marquer_notifications_lues(email):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE notifications SET lue = 1 WHERE destinataire_email = ?", (email,))
    connection.commit()
    connection.close()

# ---------------------------------------------------------------------------
# 6. PROFIL, ABONNEMENT, VISITE DE PROFIL
# ---------------------------------------------------------------------------
def lister_posts_de(email):
    """Toutes les publications d'un utilisateur (publiques + privées) —
    pour l'affichage sur SON PROPRE profil."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM posts WHERE auteur_email = ? ORDER BY id DESC", (email,))
    posts = cursor.fetchall()
    connection.close()
    return posts


def lister_posts_publics_de(email):
    """Uniquement les publications PUBLIQUES — pour le profil public
    consulté par quelqu'un d'autre."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM posts WHERE auteur_email = ? AND visibilite = 'public' ORDER BY id DESC",
        (email,)
    )
    posts = cursor.fetchall()
    connection.close()
    return posts


def changer_visibilite_post(post_id, auteur_email):
    """Bascule un post entre public et privé (uniquement si on en est l'auteur)."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT visibilite FROM posts WHERE id = ? AND auteur_email = ?", (post_id, auteur_email))
    ligne = cursor.fetchone()
    if ligne is not None:
        nouvelle_valeur = "prive" if ligne["visibilite"] == "public" else "public"
        cursor.execute("UPDATE posts SET visibilite = ? WHERE id = ?", (nouvelle_valeur, post_id))
        connection.commit()
    connection.close()


def modifier_club(email, nom_club, logo_url, pays, ligue):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE clubs SET nom_club = ?, logo_url = ?, pays = ?, ligue = ? WHERE email = ?
    """, (nom_club, logo_url, pays, ligue, email))
    connection.commit()
    connection.close()


def modifier_particulier(email, nom, prenoms, nationalite, poste):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE particuliers SET nom = ?, prenoms = ?, nationalite = ?, poste = ? WHERE email = ?
    """, (nom, prenoms, nationalite, poste, email))
    connection.commit()
    connection.close()


def changer_langue(type_compte, email, langue):
    table = "clubs" if type_compte == "club" else "particuliers"
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"UPDATE {table} SET langue = ? WHERE email = ?", (langue, email))
    connection.commit()
    connection.close()


# --- Abonnement obligatoire : Club = 1700Fr/mois, Particulier = 750Fr/mois,
#     payable via Wave, Moov Money ou MTN Money. ---
MOYENS_DE_PAIEMENT = ["Wave", "Moov Money", "MTN Money"]


def prix_abonnement(type_compte):
    return 1700 if type_compte == "club" else 750


def abonnement_est_actif(type_compte, email):
    table = "clubs" if type_compte == "club" else "particuliers"
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"SELECT abonnement_actif FROM {table} WHERE email = ?", (email,))
    ligne = cursor.fetchone()
    connection.close()
    return ligne is not None and bool(ligne["abonnement_actif"])


def activer_abonnement(type_compte, email, moyen_paiement):
    """
    ⚠️ Paiement SIMULÉ (pas de connexion internet dans cet environnement de
    test). Pour un vrai lancement, brancher ici l'API du fournisseur choisi
    (Wave, MTN MoMo, Moov Money...) avant de marquer l'abonnement actif.
    """
    table = "clubs" if type_compte == "club" else "particuliers"
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        f"UPDATE {table} SET abonnement_actif = 1, moyen_paiement = ? WHERE email = ?",
        (moyen_paiement, email)
    )
    connection.commit()
    connection.close()


def resilier_abonnement(type_compte, email):
    table = "clubs" if type_compte == "club" else "particuliers"
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"UPDATE {table} SET abonnement_actif = 0 WHERE email = ?", (email,))
    connection.commit()
    connection.close()


def peut_visiter(mon_type, type_du_compte_visite):
    """Un Club peut visiter tout le monde ; un Particulier uniquement les Clubs."""
    if mon_type == "club":
        return True
    return type_du_compte_visite == "club"


# ---------------------------------------------------------------------------
# 7. MARKET
# ---------------------------------------------------------------------------
def peut_publier_sur_market(type_compte, utilisateur):
    """Un Club peut toujours publier. Un Particulier seulement s'il est
    Agent ou Coach (pas Joueur)."""
    if type_compte == "club":
        return True
    return utilisateur["profession"] in ("Agent", "Coach")


def creer_annonce_joueur(auteur_email, auteur_nom, logo_url, photo_joueur,
                          nom_joueur, poste, age, prix):
    connection = get_connection()
    cursor = connection.cursor()
    date_publication = datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute("""
        INSERT INTO market (type_annonce, auteur_type, auteur_email, auteur_nom, logo_url,
                             photo_url, nom_joueur, poste, age, prix, date_publication)
        VALUES ('joueur', 'club', ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (auteur_email, auteur_nom, logo_url, photo_joueur, nom_joueur, poste, age, prix, date_publication))
    connection.commit()
    connection.close()


def creer_annonce_recherche(auteur_email, auteur_nom, photo, texte_recherche):
    connection = get_connection()
    cursor = connection.cursor()
    date_publication = datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute("""
        INSERT INTO market (type_annonce, auteur_type, auteur_email, auteur_nom,
                             photo_url, description, date_publication)
        VALUES ('recherche', 'particulier', ?, ?, ?, ?, ?)
    """, (auteur_email, auteur_nom, photo, texte_recherche, date_publication))
    connection.commit()
    connection.close()


def lister_annonces_market():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM market ORDER BY id DESC")
    annonces = cursor.fetchall()
    connection.close()
    return annonces
