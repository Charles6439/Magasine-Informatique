from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import hashlib

app = Flask(__name__)
app.secret_key = "cle_secrete_magasin"

# Connected securely to your standalone MySQL engine on port 3306
db = mysql.connector.connect(
    host="127.0.0.1", 
    port="3306", 
    user="root", 
    password="", 
    database="magasin_informatique"
)

@app.route("/")
def accueil():
    return render_template("accueil.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        # Hash the user input using SHA-256 to safely match the database hashes
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cursor = db.cursor(dictionary=True)
        
        # Compare email and the HASHED password
        cursor.execute("SELECT * FROM clients WHERE email = %s AND password = %s", (email, hashed_password))
        client = cursor.fetchone()
        
        if client:
            session["client_id"] = client["id"]
            return redirect(url_for("client", id_client=client["id"]))
        return "Identifiants incorrects"
    return render_template("login.html")

@app.route("/client/<int:id_client>")
def client(id_client):
    cursor = db.cursor(dictionary=True, buffered=True)
    cursor.execute("""
        SELECT produits.nom AS nom, 
               produits.prix AS prix, 
               details_commandes.quantite AS quantite
        FROM details_commandes
        JOIN produits ON details_commandes.id_product = produits.id
        JOIN commandes ON details_commandes.id_commande = commandes.id
        WHERE commandes.id_client = %s
    """, (id_client,))
    produits = cursor.fetchall()
    return render_template("client.html", produits=produits)

if __name__ == "__main__":
    app.run(debug=True)