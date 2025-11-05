from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html", title="Accueil")

@app.route("/catalogue")
def catalogue():
    return render_template("catalogue.html", title="Catalogue")

@app.route("/propos")
def propos():
    return render_template("propos.html", title="À propos")

@app.route("/contact")
def contact():
    return render_template("contact.html", title="Contact")

@app.route("/connexion")
def login():
    return render_template("login.html", title="Connexion")

@app.route("/deconnexion")
def logout():
    return render_template("logout.html", title="Déconnexion")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", title="Dashboard")


@app.route("/dashboard/adherents")
def adherents():
    return render_template("adherents.html", title="Adhérents")


@app.route("/dashboard/emprunts")
def emprunts():
    return render_template("emprunts.html", title="Emprunts")


@app.route("/dashboard/statistiques")
def statistiques():
    return render_template("statistiques.html", title="Statistiques")


@app.route("/dashboard/parametres")
def parametres():
    return render_template("parametres.html", title="Paramètres")



if __name__ == "__main__":
    app.run(debug=True)
