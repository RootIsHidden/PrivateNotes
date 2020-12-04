# ===============================================================================================================
# Private Notes Web Application (v. 1.0)
# ---------------------------------------------------------------------------------------------------------------
# Developed by Nikolai Korolkov, University of Central Florida, December 2020
# ---------------------------------------------------------------------------------------------------------------
# Please, read 'license.txt' for additional detaiils
# ===============================================================================================================

from flask import Flask, render_template, flash, abort, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_security import Security, SQLAlchemyUserDatastore, login_required, auth_required, UserMixin, RoleMixin
from flask_login import current_user, login_required
from datetime import datetime
import os, psycopg2, wtf_helpers, zxcvbn

app = Flask(__name__)
# Configuring secret data from environment vars (added to git ignore):
app.config['SECRET_KEY']              = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SECURITY_PASSWORD_SALT']  = os.environ['PASSWORD_SALT']
# flask_security configurations:
app.config['SECURITY_PASSWORD_COMPLEXITY_CHECKER'] = zxcvbn
app.config['SECURITY_PASSWORD_LENGTH_MIN'] = 15
app.config['PREFERRED_URL_SCHEME'] = 'https'

# Have cookie sent
app.config['SECURITY_CSRF_COOKIE'] = {'key': 'XSRF-TOKEN'}
# Don't have csrf tokens expire (they are invalid after logout)
app.config['WTF_CSRF_TIME_LIMIT'] = None
# You can't get the cookie until you are logged in.
app.config['WTF_CSRF_CHECK_DEFAULT'] = False
app.config['SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS'] = True
# Enable CSRF protection
CSRFProtect(app)

app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_CHANGEABLE'] = True
app.config['SECURITY_POST_LOGIN_VIEW'] =    '/who'
app.config['SECURITY_POST_REGISTER_VIEW'] = '/who'
app.config['SECURITY_POST_CHANGE_VIEW'] =   '/who'

app.config['SECURITY_FLASH_MESSAGES'] = True
app.config['SECURITY_DEFAULT_REMEMBER_ME'] = False
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_SEND_PASSWORD_CHANGE_EMAIL'] = False
app.config['SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL'] = False
# DB connection checker:
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Creating a DB instance
db = SQLAlchemy(app)
# Creating a new table for implementing roles
roles_users = db.Table('roles_users', db.Column('user_id', db.Integer(), db.ForeignKey('user.id')), \
                db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

# User class
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    # Adding note-user (aka many to one) relationship:
    notes = db.relationship('Note', backref='user', lazy='dynamic')

# Role class used for access-control:
class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

# FlaskForm class
class NoteForm(FlaskForm):
    # Note's category:
    category_str_field  = StringField('Category (Optional)')
    # Note's title:
    title_str_field     = StringField('Title', validators=[DataRequired()])
    # Note's content:
    str_field           = StringField('Note', validators=[DataRequired()])
    # Add note button:
    submit_Button = SubmitField('Add Note')

# Edit-FlaskForm class
class EditNoteForm(FlaskForm):
    # Note's category:
    category_str_field  = StringField('Category')
    # Note's title:
    title_str_field     = StringField('Title', validators=[DataRequired()])
    # Note's content:
    str_field           = StringField('Note', validators=[DataRequired()])
    # Add note button:
    submit_button = SubmitField('Edit Note')

# Note class
class Note(db.Model):
    id         = db.Column(db.Integer, primary_key = True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'))
    date       = db.Column(db.String(128), unique = False, nullable = False)
    title      = db.Column(db.String(256), unique = False, nullable = False)
    category   = db.Column(db.String(256), unique = False, nullable = False)
    text       = db.Column(db.String(2048), unique = False, nullable = False)

    # Modyfying the constructor:
    def __init__(self, note, user):
        self.text    = note
        self.user_id = user.id
    
    def __repr__(self):
        return '<Note %r>' % self.id

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)
db.create_all()
Bootstrap(app)
wtf_helpers.add_helpers(app)

# Default page
@app.route("/")
def index():
    users = User.query
    return render_template("index.html", users=users)


@app.route('/who')
@auth_required('token', 'session')
def who():
    if current_user.is_authenticated:
        flash("Succesfully redirected.", "success")
        return redirect(url_for('notes', user_email=current_user.email, sorting_mode='Date'))
    else:
        abort(403)
    
# User's directory page:
@app.route('/notes/<user_email>/<sorting_mode>', methods = ['GET', 'POST'])
@app.route('/notes/<user_email>', defaults={'sorting_mode' : 'Date'}, methods = ['GET', 'POST'])
@auth_required('token', 'session')
def notes(user_email, sorting_mode):
    user = User.query.filter_by(email=user_email).first_or_404()

    if user != current_user:
        abort(403)

    # Checking whether user is logged in: 
    if user == current_user:
        form = NoteForm()
    else:
        form = None

    if form and form.validate_on_submit():
        # Setting up DB object having a user refference:
        note            = Note(form.str_field.data, user)
        note.date       = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        note.title      = form.title_str_field.data
        
        category  = form.category_str_field.data
        if category:
            note.category = category
        else:
            note.category = '-'

        form.category_str_field.data = ""
        form.title_str_field.data = ""
        form.str_field.data = ""

        # Adding a Note to DB:
        db.session.add(note)
        db.session.commit()
        flash("The Private Note was added.", "success")
    
    # Sorting:
    if sorting_mode == 'Date':
        notesList = user.notes.order_by(Note.date)
    elif sorting_mode == 'Title':
        notesList = user.notes.order_by(Note.title)
    elif sorting_mode == 'Category':
        notesList = user.notes.order_by(Note.category)
    else:
        abort(403)

    return render_template('notes.html', form = form, notesList = notesList, user_email=user_email, sorting_mode = sorting_mode)

@app.route("/edit_note/<note_id>", methods=["GET", "POST"])
@auth_required('token', 'session')
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)

    if note.user_id != current_user.id:
        abort(403)

    form = EditNoteForm()

    if request.method == 'GET':
        form.category_str_field.data = note.category
        form.title_str_field.data    = note.title
        form.str_field.data          = note.text

    if form.validate_on_submit():
        note.category = form.category_str_field.data
        note.title    = form.title_str_field.data
        note.text     = form.str_field.data
        note.date     = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        db.session.commit()
        flash("The Private Note was edited.", "success")
        return redirect(url_for('notes', user_email=current_user.email, sorting_mode='Date'))

    return render_template('edit_note.html', form = form)

@app.route("/delete_note/<note_id>", methods=["GET", "POST"])
@auth_required('token', 'session')
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)

    if note.user_id != current_user.id:
        abort(403)

    db.session.delete(note)
    db.session.commit()
    flash("The Private Note was deleted.", "success")
    return redirect(url_for('notes', user_email=current_user.email, sorting_mode='Date'))

if __name__ == '__main__':
    app.run()
