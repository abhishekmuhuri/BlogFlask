from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc, ForeignKey
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField
from wtforms.validators import DataRequired, URL, Email, ValidationError
from flask_ckeditor import CKEditor, CKEditorField
import datetime
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from os import environ

app = Flask(__name__)
app.config['SECRET_KEY'] = environ.get('FLASK_KEY')
app.config['EXPOSE_PORT'] = environ.get('EXPOSE_PORT')
# app.config['SECRET_KEY'] = 'CM9n5vsfm5'
app.config['SESSION_PERMANENT'] = False

EXPOSE_PORT = environ.get('EXPOSE_PORT')

# Initialise the CKEditor so that you can use it in make_post.html
ckeditor = CKEditor(app)
Bootstrap5(app)

# Initialize the main SQLAlchemy instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy()

app.config['SQLALCHEMY_BINDS'] = {
    'users': 'sqlite:///users.db',
}
db.init_app(app)

# LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# CONFIGURE TABLE

# USER TABLE
class User(db.Model, UserMixin):
    __bind_key__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)


# Blog Table
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey(User.id), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


# Custom validator function to check for characters only
def characters_only(form, field):
    value = field.data
    if not value.isalpha():
        raise ValidationError('Only characters are allowed.')


def unique_email(form, field):
    value = field.data
    user = User.query.filter_by(email=value).first()
    if user:
        raise ValidationError('Email already registered. Try signing in')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class LoginForm(FlaskForm):
    email = EmailField('email', validators=[DataRequired(), Email()])
    password = PasswordField('password', [DataRequired()])
    submit_button = SubmitField('Login')


class Registration(FlaskForm):
    email = EmailField('email', validators=[DataRequired(), Email(), unique_email])
    password = PasswordField('password', validators=[DataRequired()])
    name = StringField('name', validators=[DataRequired(), characters_only])
    submit_button = SubmitField('Register')


with app.app_context():
    db.create_all()


# WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    # Notice body is using a CKEditorField and not a StringField
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    if current_user.is_authenticated:
        return render_template("index.html", all_posts=posts, user_authenticated=True, user=current_user)
    else:
        return render_template("index.html", all_posts=posts, user_authenticated=False)


@app.route("/post/<int:post_id>")
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    if current_user.is_authenticated:
        user_authenticated = True
    else:
        user_authenticated = False
    return render_template("post.html", post=requested_post, user_authenticated=user_authenticated, user=current_user)


@app.route("/delete/<int:post_id>")
@login_required
def delete(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    # Check if current user is the owner of blog post
    if requested_post.user_id == current_user.id or current_user.is_admin is True:
        db.session.delete(requested_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))

    else:
        error_response = {
            "error": "Not authorized to delete this post"
        }
        return jsonify(error_response), 401


@app.route("/edit-post/<int:post_id>", methods=["POST", "GET"])
@login_required
def edit_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    # If user_id not equals current user_id or not admin
    if requested_post.user_id != current_user.id and current_user.is_admin is not True:
        error_response = {"error": "User not authorised to edit this post"}
        return jsonify(error_response), 401

    edit_form = CreatePostForm(
        title=requested_post.title,
        subtitle=requested_post.subtitle,
        img_url=requested_post.img_url,
        author=requested_post.author,
        body=requested_post.body
    )
    if edit_form.validate_on_submit():
        requested_post.title = edit_form.title.data
        requested_post.subtitle = edit_form.subtitle.data
        requested_post.body = edit_form.body.data
        requested_post.author = edit_form.author.data
        requested_post.img_url = edit_form.img_url.data
        try:
            db.session.commit()
            flash("Blog post created successfully.", "success")
            return redirect(url_for("get_all_posts"))
        except exc.IntegrityError:
            db.session.rollback()
            return jsonify(response={"ERROR": "Same Blog already exists"}), 403

    return render_template("make-post.html", form=edit_form, is_edit=True, user_authenticated=True, user=current_user)


# Adding a new Post
@app.route("/new-post", methods=["GET", "POST"])
@login_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost()
        new_post.title = form.title.data
        new_post.subtitle = form.subtitle.data
        new_post.body = form.body.data
        new_post.author = form.author.data
        new_post.img_url = form.img_url.data
        date = datetime.datetime.now()
        date = date.strftime("%B %d, %Y")
        new_post.date = date
        new_post.user_id = current_user.id
        try:
            db.session.add(new_post)
            db.session.commit()
            flash("Blog post created successfully.", "success")
            return redirect(url_for("get_all_posts"))
        except exc.IntegrityError:
            db.session.rollback()
            return jsonify(response={"ERROR": "Same Blog already exists"}), 403

    return render_template("make-post.html", form=form, user_authenticated=True, user=current_user)


@app.route("/about")
def about():
    print("ABOUT SELECTED")
    if current_user.is_authenticated:
        user_authenticated = True
    else:
        user_authenticated = False
    return render_template("about.html", user_authenticated=user_authenticated, user=current_user)


@app.route("/contact")
def contact():
    if current_user.is_authenticated:
        user_authenticated = True
    else:
        user_authenticated = False
    return render_template("contact.html", user_authenticated=user_authenticated, user=current_user)


@app.route('/register', methods=["POST", "GET"])
def register():
    register_form = Registration()
    if current_user.is_authenticated:  # Check if the user is already logged in
        return redirect(url_for('get_all_posts'))

    if register_form.validate_on_submit():
        new_user = User()
        password = register_form.password.data
        hash_and_salted_pass = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        new_user.password = hash_and_salted_pass
        new_user.name = register_form.name.data
        new_user.email = register_form.email.data
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful")
            login_user(new_user)
            return redirect(url_for("get_all_posts"))
        except:
            print("ERROR OCCURRED")
            db.session.rollback()
            flash("ERROR OCCURRED", "danger")
    return render_template("register.html", form=register_form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.")
    return redirect(url_for("get_all_posts"))


@app.route('/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:  # Check if the user is already logged in
        return redirect(url_for('get_all_posts'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Logged in successfully.")
            print(f"User logged in {user.name}")
            return redirect(url_for("get_all_posts"))
        else:
            flash("Wrong username or password!")
    return render_template("login.html", form=form, user_authenticated=False)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=EXPOSE_PORT)
