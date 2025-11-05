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


if __name__ == "__main__":
    app.run(debug=True)
