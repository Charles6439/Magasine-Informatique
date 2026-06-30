import os  # Ajoutez cette ligne ici
from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL

app = Flask(__name__)

# Database Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = os.environ.get('DB_PASSWORD')
app.config['MYSQL_DB'] = 'techsecure_db'
app.config['MYSQL_PORT'] = 3306    # Update to 3307 if 3306 fails

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/branch/<name>')
def branch_detail(name):
    # Get the cursor from your 'mysql' object
    cur = mysql.connection.cursor()
    # Use the safe parameterized query
    query = "SELECT * FROM branches WHERE branch_name = %s"
    cur.execute(query, (name,))
    branch = cur.fetchone()
    cur.close()
    return render_template('branch.html', branch=branch)
@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/branches')
def branches():
    import MySQLdb
    # This makes the data behave like a dictionary
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM branches")
    data = cur.fetchall()
    cur.close()
    return render_template('branches.html', branches=data)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO contacts (sender_name, sender_email, subject, message) VALUES (%s, %s, %s, %s)", 
                    (name, email, subject, message))
        mysql.connection.commit()
        cur.close()
        # This replaces your old "Message sent successfully!" text
        return redirect(url_for('thankyou')) 
    return render_template('contact.html')
@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')
if __name__ == '__main__':
    app.run(debug=True)