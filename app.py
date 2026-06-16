from flask import Flask, render_template, request, redirect, url_for, session, flash
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

@app.route("/client/<int:id_client>/commander", methods=["GET", "POST"])
def commander(id_client):
    cursor = db.cursor(dictionary=True, buffered=True)

    # --- GET Method: Show the ordering page ---
    if request.method == "GET":
        # Fetch products that actually have stock available
        cursor.execute("SELECT id, nom, prix, stock FROM produits WHERE stock > 0")
        produits = cursor.fetchall()
        return render_template("commander.html", produits=produits, id_client=id_client)

    # --- POST Method: Handle the form submission ---
    if request.method == "POST":
        id_produit = int(request.form["id_produit"])
        quantite_demandee = int(request.form["quantite"])

        # 1. Verify the product availability and stock level
        cursor.execute("SELECT nom, stock FROM produits WHERE id = %s", (id_produit,))
        produit = cursor.fetchone()

        if not produit or produit["stock"] < quantite_demandee:
            flash(f"Stock insuffisant. Seulement {produit['stock'] if produit else 0} restant(s).")
            return redirect(url_for("commander", id_client=id_client))

        try:
            # 2. Create an order instance inside the 'commandes' table
            cursor.execute(
                "INSERT INTO commandes (id_client, date_commande) VALUES (%s, NOW())", 
                (id_client,)
            )
            id_nouvelle_commande = cursor.lastrowid  # Retrieve the generated order ID

            # 3. Add item breakdown details into 'details_commandes'
            cursor.execute(
                "INSERT INTO details_commandes (id_commande, id_product, quantite) VALUES (%s, %s, %s)",
                (id_nouvelle_commande, id_produit, quantite_demandee)
            )

            # 4. Deduct the purchased stock quantity from the inventory
            cursor.execute(
                "UPDATE produits SET stock = stock - %s WHERE id = %s",
                (quantite_demandee, id_produit)
            )

            # Commit everything safely to the database
            db.commit()

        except Exception as e:
            db.rollback()  # Undo changes if anything fails
            flash("Une erreur est survenue lors de l'enregistrement de votre commande.")
            return redirect(url_for("commander", id_client=id_client))

        # 5. Success! Send the user back to their dashboard space
        return redirect(url_for("client", id_client=id_client))

# This block is perfectly positioned at the absolute end
if __name__ == "__main__":
    app.run(debug=True)