from flask import Flask, render_template, request, redirect, url_for, session
from datetime import date
import mysql.connector, hashlib

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def get_db():
    return mysql.connector.connect(host="localhost", user="root", password="", database="magasin_informatique")

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email, pwd = request.form["email"], request.form["password"]
        
        # We hash the input here so it matches the hashed format in the database
        hashed_pwd = hashlib.md5(pwd.encode()).hexdigest()
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM clients WHERE email = %s AND password = %s", (email, hashed_pwd))
        user = cursor.fetchone()
        db.close()
        
        if user:
            session["user_id"] = user["id"]
            return redirect(url_for('client', id_client=user["id"]))
        return "Login failed: Incorrect email or password."
    return render_template("login.html")

@app.route("/client/<int:id_client>")
def client(id_client):
    if "user_id" not in session: return redirect(url_for('login'))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT p.nom, p.prix, dc.quantite FROM produits p JOIN details_commandes dc ON p.id = dc.id_product JOIN commandes c ON dc.id_commande = c.id WHERE c.id_client = %s", (id_client,))
    produits = cursor.fetchall()
    db.close()
    return render_template("client.html", produits=produits, id_client=id_client)

@app.route("/commander/<int:id_client>", methods=["GET", "POST"])
def commander(id_client):
    if "user_id" not in session: return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    # Get all products to display in the list
    cursor.execute("SELECT * FROM produits")
    produits = cursor.fetchall()
    db.close()
    
    return render_template("commander.html", id_client=id_client, produits=produits)


    # AJOUTER AU PANIER
@app.route("/ajouter_panier/<int:id_client>/<int:id_produit>")
def ajouter_panier(id_client, id_produit):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Check if product exists and get stock
    cursor.execute("SELECT stock FROM produits WHERE id = %s", (id_produit,))
    produit = cursor.fetchone()
    
    if not produit:
        cursor.close()
        db.close()
        return "Produit introuvable"

    # Check if already in cart
    cursor.execute("SELECT * FROM panier WHERE id_client = %s AND id_produit = %s", (id_client, id_produit))
    article = cursor.fetchone()

    if article:
        # Increment quantity
        if article["quantite"] >= produit["stock"]:
            cursor.close()
            db.close()
            return "Stock insuffisant"
        cursor.execute("UPDATE panier SET quantite = quantite + 1 WHERE id_client = %s AND id_produit = %s", (id_client, id_produit))
    else:
        # Add new item
        if produit["stock"] <= 0:
            cursor.close()
            db.close()
            return "Stock insuffisant"
        cursor.execute("INSERT INTO panier(id_client, id_produit, quantite) VALUES(%s, %s, %s)", (id_client, id_produit, 1))

    db.commit()
    cursor.close()
    db.close()
    return redirect(f"/panier/{id_client}")


# AFFICHER LE PANIER
@app.route("/panier/<int:id_client>")
def panier(id_client):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    # Get products in the cart for this client
    cursor.execute("""
        SELECT produits.nom, produits.prix, panier.quantite, (produits.prix * panier.quantite) AS total
        FROM panier
        JOIN produits ON panier.id_produit = produits.id
        WHERE panier.id_client = %s
    """, (id_client,))
    produits = cursor.fetchall()
    
    # Calculate grand total
    total_panier = sum(item['total'] for item in produits)
    
    cursor.close()
    db.close()
    return render_template("panier.html", produits=produits, total_panier=total_panier, id_client=id_client)
# PAIEMENT
# PAIEMENT
@app.route("/paiement/<int:id_client>", methods=["GET", "POST"])
def paiement(id_client):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT panier.id_produit, produits.nom, produits.prix, produits.stock, 
               panier.quantite, produits.prix * panier.quantite AS total
        FROM panier
        JOIN produits ON produits.id = panier.id_produit
        WHERE panier.id_client = %s
    """, (id_client,))
    produits = cursor.fetchall()
    total_panier = sum(produit["total"] for produit in produits)

    if request.method == "POST":
        nom = request.form["nom"].strip()
        numero = request.form["numero"].replace(" ", "").replace("-", "")
        
        cursor.execute("""
            INSERT INTO commandes (id_client, date_commande, total, statut)
            VALUES (%s, %s, %s, %s)
        """, (id_client, date.today(), total_panier, "Validée"))
        id_commande = cursor.lastrowid
        
        for produit in produits:
            cursor.execute("""
                INSERT INTO details_commandes (id_commande, id_product, quantite, prix_unitaire)
                VALUES (%s, %s, %s, %s)
            """, (id_commande, produit["id_produit"], produit["quantite"], produit["prix"]))
            
            cursor.execute("UPDATE produits SET stock = stock - %s WHERE id = %s", 
                           (produit["quantite"], produit["id_produit"]))
        
        cursor.execute("DELETE FROM panier WHERE id_client = %s", (id_client,))
        db.commit()
        cursor.close()
        db.close()
        
        return render_template("confirmation.html", nom=nom, id_client=id_client, 
                               id_commande=id_commande, total_panier=total_panier, 
                               carte=numero[-4:])

    cursor.close()
    db.close()
    return render_template("paiement.html", id_client=id_client, produits=produits, total_panier=total_panier)
if __name__ == "__main__":
    app.run(debug=True)