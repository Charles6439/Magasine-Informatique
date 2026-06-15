from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "cle_secrete_magasin"

db = mysql.connector.connect(
    host="127.0.0.1", port="3306", user="root", password="", database="magasin_informatique"
)

@app.route("/")
def accueil():
    return render_template("accueil.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM clients WHERE email = %s AND password = %s", (email, password))
        client = cursor.fetchone()
        if client:
            session["client_id"] = client["id"]
            return redirect(url_for("client", id_client=client["id"]))
        return "Identifiants incorrects"
    return render_template("login.html")

@app.route("/client/<int:id_client>")
def client(id_client):
    cursor = db.cursor(dictionary=True, buffered=True)
    # Using 'AS' tags matches the columns perfectly with your HTML variables (p.nom, p.prix, p.quantite)
    cursor.execute("""
        SELECT produits.nom AS nom, 
               produits.prix AS prix, 
               details_commandes.quantite AS quantite
        FROM commandes
        JOIN details_commandes ON commandes.id = details_commandes.id_commande
        JOIN produits ON produits.id = details_commandes.id_product
        WHERE commandes.id_client = %s
    """, (id_client,))
    produits = cursor.fetchall()
    # Sending it as 'produits' matches your Jinja loop: {% for p in produits %}
    return render_template("client.html", produits=produits)