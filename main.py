from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask_migrate import Migrate


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/bibliotheque'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'votre_cle_secrete'

# Initialisation de SQLAlchemy
db = SQLAlchemy(app)
migrate = Migrate(app, db)

UPLOAD_FOLDER = "static/livres/"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# User loader pour Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Modèles
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))  # Augmenté la taille pour le hash
    role = db.Column(db.String(20), default='user')  # 'admin' ou 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        print(f"Nouveau hash créé: {self.password_hash}")
        
    def check_password(self, password):
        if not self.password_hash or not password:
            print("Erreur: password_hash ou password est vide")
            return False
        result = check_password_hash(self.password_hash, password)
        print(f"Vérification du mot de passe:")
        print(f"Hash stocké   : {self.password_hash}")
        print(f"Mot de passe : {password}")
        print(f"Résultat     : {'Succès' if result else 'Échec'}")
        return result

class Adherent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telephone = db.Column(db.String(20))
    classe = db.Column(db.String(50))  # <- ajout de la classe
    date_inscription = db.Column(db.DateTime, default=datetime.utcnow)
    emprunts = db.relationship('Emprunt', backref='adherent', lazy=True)

class Livre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    auteur = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(13), unique=True)
    annee_publication = db.Column(db.Integer)
    categorie = db.Column(db.String(50))

    resume = db.Column(db.Text)  # ✅ Résumé du livre
    contenu_pdf = db.Column(db.String(255))  # ✅ Fichier PDF uploadé

    disponible = db.Column(db.Boolean, default=True)
    emprunts = db.relationship('Emprunt', backref='livre', lazy=True)

class Emprunt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    adherent_id = db.Column(db.Integer, db.ForeignKey('adherent.id'), nullable=False)
    livre_id = db.Column(db.Integer, db.ForeignKey('livre.id'), nullable=False)
    date_emprunt = db.Column(db.DateTime, default=datetime.utcnow)
    date_retour_prevue = db.Column(db.DateTime, nullable=False)
    date_retour_effective = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='en_cours')  # en_cours, retourne, retard

# Route pour créer un admin (à retirer en production)
@app.route('/setup/admin', methods=['GET', 'POST'])
def setup_admin():
    if User.query.filter_by(role='admin').first():
        flash('Un administrateur existe déjà', 'warning')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        admin = User(
            username=request.form['username'],
            email=request.form['email'],
            role='admin'
        )
        admin.set_password(request.form['password'])
        db.session.add(admin)
        db.session.commit()
        flash('Administrateur créé avec succès', 'success')
        return redirect(url_for('login'))
    
    return render_template('setup_admin.html', title='Créer un administrateur')

# Création des tables
with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return render_template("index.html", title="Accueil")

@app.route("/catalogue", methods=['GET', 'POST'])
def catalogue():
    if request.method == 'POST':
        nouveau_livre = Livre(
            titre=request.form['titre'],
            auteur=request.form['auteur'],
            isbn=request.form['isbn'],
            annee_publication=request.form['annee'],
            categorie=request.form['categorie']
        )
        db.session.add(nouveau_livre)
        db.session.commit()
        return redirect(url_for('catalogue'))
    
    livres = Livre.query.all()
    return render_template("catalogue.html", title="Catalogue", livres=livres)

@app.route("/propos")
def propos():
    return render_template("propos.html", title="À propos")

@app.route("/contact")
def contact():
    return render_template("contact.html", title="Contact")

@app.route("/inscription", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Vérifications
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur est déjà pris', 'danger')
            return render_template('register.html', title='Inscription')
            
        if User.query.filter_by(email=email).first():
            flash('Cette adresse email est déjà utilisée', 'danger')
            return render_template('register.html', title='Inscription')
            
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas', 'danger')
            return render_template('register.html', title='Inscription')
            
        # Création du nouvel utilisateur
        user = User(username=username, email=email, role='user')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Inscription réussie ! Vous pouvez maintenant vous connecter', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html', title='Inscription')

@app.route("/connexion", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Tentative de connexion - Username: {username}")
        
        user = User.query.filter_by(username=username).first()
        print(f"Utilisateur trouvé: {user is not None}")
        
        if user:
            # Utilisation de la méthode check_password de la classe User
            if user.check_password(password):
                login_user(user)
                flash('Connexion réussie!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                print(f"Hash stocké: {user.password_hash}")
                print(f"Mot de passe fourni: {password}")
                flash('Mot de passe incorrect', 'danger')
        else:
            flash('Nom d\'utilisateur non trouvé', 'danger')
    
    return render_template("login.html", title="Connexion")

@app.route("/deconnexion")
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('index'))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", title="Dashboard", user=current_user)


@app.route("/dashboard/adherents", methods=['GET', 'POST'])
@login_required
def adherents():
    if request.method == 'POST':
        nouveau_adherent = Adherent(
            nom=request.form['nom'],
            prenom=request.form['prenom'],
            email=request.form['email'],
            telephone=request.form['telephone'],
            classe=request.form.get('classe')  # <- ajout ici
        )
        db.session.add(nouveau_adherent)
        db.session.commit()
        return redirect(url_for('adherents'))
    
    adherents_liste = Adherent.query.all()
    return render_template("adherents.html", title="Adhérents", adherents=adherents_liste)


@app.route("/dashboard/emprunts", methods=['GET', 'POST'])
@login_required
def emprunts():
    if request.method == 'POST':
        try:
            adherent_id = int(request.form['adherent_id'])
            livre_id = int(request.form['livre_id'])
            date_retour_str = request.form['date_retour']
            date_retour_prevue = datetime.strptime(date_retour_str, '%Y-%m-%d')
        except (ValueError, KeyError):
            # Gérer l'erreur : champs manquants ou format incorrect
            return "Données invalides", 400

        livre = Livre.query.get(livre_id)
        if not livre or not livre.disponible:
            return "Livre non disponible", 400

        nouvel_emprunt = Emprunt(
            adherent_id=adherent_id,
            livre_id=livre_id,
            date_retour_prevue=date_retour_prevue
        )

        livre.disponible = False  # Marquer le livre comme emprunté
        db.session.add(nouvel_emprunt)
        db.session.commit()

        return redirect(url_for('emprunts'))

    # Requêtes pour l'affichage
    emprunts_liste = Emprunt.query.all()
    adherents_liste = Adherent.query.all()
    livres_disponibles = Livre.query.filter_by(disponible=True).all()

    # Exemple de réservations fictives
    reservations_liste = [
        {
            'livre': Livre.query.first(),
            'adherent': Adherent.query.first(),
            'date_reservation': datetime.utcnow(),
            'priorite': 1,
            'status': 'en_attente'
        }
    ]

    # 🔧 Ici on passe l'heure actuelle sans parenthèses à utiliser dans le template
    return render_template(
        "emprunts.html",
        title="Emprunts",
        emprunts=emprunts_liste,
        adherents=adherents_liste,
        livres=livres_disponibles,
        reservations=reservations_liste,
        now=datetime.utcnow()  # on passe l'objet datetime ici
    )

@app.route("/dashboard/livres", methods=['GET', 'POST'])
@login_required
def livres():
    if current_user.role != "admin":
        flash("Accès non autorisé", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        titre = request.form['titre']
        auteur = request.form['auteur']
        isbn = request.form['isbn']
        annee = request.form['annee_publication']
        categorie = request.form['categorie']
        resume = request.form['resume']

        # ✅ FICHIER PDF
        fichier = request.files.get("contenu_pdf")
        fichier_nom = None

        if fichier:
            fichier_nom = secure_filename(fichier.filename)
            fichier.save(os.path.join(app.config['UPLOAD_FOLDER'], fichier_nom))

        nouveau_livre = Livre(
            titre=titre,
            auteur=auteur,
            isbn=isbn,
            annee_publication=annee,
            categorie=categorie,
            resume=resume,
            contenu_pdf=fichier_nom
        )

        db.session.add(nouveau_livre)
        db.session.commit()

        flash("Livre ajouté avec succès", "success")
        return redirect(url_for("livres"))

    livres_liste = Livre.query.all()
    return render_template("livres.html", title="Livres", livres=livres_liste)

@app.route("/dashboard/emprunts/retour/<int:emprunt_id>")
@login_required
def retourner_livre(emprunt_id):
    emprunt = Emprunt.query.get_or_404(emprunt_id)
    emprunt.status = 'retourne'
    emprunt.date_retour_effective = datetime.utcnow()
    emprunt.livre.disponible = True
    db.session.commit()
    return redirect(url_for('emprunts'))


@app.route("/dashboard/statistiques")
@login_required
def statistiques():
    total_adherents = Adherent.query.count()
    total_livres = Livre.query.count()
    emprunts_en_cours = Emprunt.query.filter_by(status='en_cours').count()
    livres_disponibles = Livre.query.filter_by(disponible=True).count()
    
    # Calcul du taux de disponibilité
    taux_disponibilite = round((livres_disponibles / total_livres * 100) if total_livres > 0 else 100)
    
    # Statistiques des emprunts par catégorie avec pourcentages pré-calculés
    emprunts_par_categorie = db.session.query(
        Livre.categorie, 
        db.func.count(Emprunt.id).label('count')
    ).join(Emprunt).group_by(Livre.categorie).all()
    
    stats_categories = []
    for categorie, count in emprunts_par_categorie:
        pourcentage = round((count / emprunts_en_cours * 100) if emprunts_en_cours > 0 else 0)
        stats_categories.append({
            'categorie': categorie,
            'count': count,
            'pourcentage': pourcentage
        })
    
    # Adhérents les plus actifs avec pourcentages pré-calculés
    adherents_actifs = db.session.query(
        Adherent,
        db.func.count(Emprunt.id).label('total_emprunts')
    ).join(Emprunt).group_by(Adherent).order_by(db.text('total_emprunts DESC')).limit(5).all()
    
    stats_adherents = []
    max_emprunts = max([total for _, total in adherents_actifs]) if adherents_actifs else 1
    for adherent, total in adherents_actifs:
        pourcentage = round((total / max_emprunts * 100))
        stats_adherents.append({
            'adherent': adherent,
            'total': total,
            'pourcentage': pourcentage
        })
    
    return render_template("statistiques.html", 
                         title="Statistiques",
                         total_adherents=total_adherents,
                         total_livres=total_livres,
                         emprunts_en_cours=emprunts_en_cours,
                         livres_disponibles=livres_disponibles,
                         taux_disponibilite=taux_disponibilite,
                         stats_categories=stats_categories,
                         stats_adherents=stats_adherents)


@app.route("/dashboard/parametres")
def parametres():
    return render_template("parametres.html", title="Paramètres")



if __name__ == "__main__":
    app.run(debug=True)
