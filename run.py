"""
run.py
------
Point de départ pour lancer l'application en local :

    python run.py

Ouvre ensuite ton navigateur à l'adresse http://127.0.0.1:5000
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
