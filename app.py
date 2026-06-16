from flask import Flask, render_template, request, redirect, url_for, session
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
    if request.method == "POST": return "Commande validée !"
    return render_template("commander.html", id_client=id_client)

if __name__ == "__main__":
    app.run(debug=True)