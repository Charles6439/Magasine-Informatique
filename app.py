from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# Replace with your actual database credentials
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="magasin_informatique"
)

@app.route("/client/<int:id_client>")
def client(id_client):
    cursor = db.cursor(dictionary=True, buffered=True)
    cursor.execute("""
        SELECT p.nom, p.prix, dc.quantite 
        FROM produits p
        JOIN details_commandes dc ON p.id = dc.id_product
        JOIN commandes c ON dc.id_commande = c.id
        WHERE c.id_client = %s
    """, (id_client,))
    produits = cursor.fetchall()
    return render_template("client.html", produits=produits, id_client=id_client)

@app.route("/client/<int:id_client>/commander", methods=["GET", "POST"])
def commander(id_client):
    cursor = db.cursor(dictionary=True, buffered=True)
    if request.method == "POST":
        id_produit = request.form.get("id_produit")
        quantite = int(request.form.get("quantite"))
        
        # Simple placeholder insert to test connectivity
        cursor.execute("INSERT INTO commandes (id_client, total) VALUES (%s, 0)", (id_client,))
        db.commit()
        return redirect(url_for('client', id_client=id_client))

    cursor.execute("SELECT * FROM produits")
    return render_template("commander.html", produits=cursor.fetchall(), id_client=id_client)

if __name__ == "__main__":
    app.run(debug=True)