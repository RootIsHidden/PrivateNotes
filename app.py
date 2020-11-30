# ===============================================================================================================
# Private Notes Web Application
# ---------------------------------------------------------------------------------------------------------------
# Nikolai Korolkov, University of Central Florida, December 2020.
# ---------------------------------------------------------------------------------------------------------------
# NOTE:
# The source code is partially based on Alexander Putilin's youTube series and implementation, which was released
# under MIT licence (permissive). Thank you, Alexander, for providing me with opportunity to learn from you! UI 
# files came fron open-sources under permissive licenses as well. Alexander Putilin granted me a written
# permission to rely on his videos and implementation for educational purposes.
# ===============================================================================================================

from flask import Flask, render_template, flash, abort, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_security import Security, SQLAlchemyUserDatastore, login_required, UserMixin, RoleMixin
from flask_login import current_user, login_required
from datetime import datetime
import os
import psycopg2
import wtf_helpers

app = Flask(__name__)
# Configuring KEYs from env vars:
app.config['SECRET_KEY'] = 'devkey'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
# flask_security configurations:
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_CHANGEABLE'] = True
app.config['SECURITY_FLASH_MESSAGES'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_SEND_PASSWORD_CHANGE_EMAIL'] = False
app.config['SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL'] = False
# To be changed in Production server!!!!!! :)
app.config['SECURITY_PASSWORD_SALT'] = 'sJ$_MeLa$G9*KVe43@xV'
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

# Form class
class NoteForm(Form):
    # Note's category:
    category_str_field  = StringField('Category (Optional)')
    # Note's title:
    title_str_field     = StringField('Title', validators=[DataRequired()])
    # Note's content:
    str_field           = StringField('Note', validators=[DataRequired()])
    # Add note button:
    submit_Button = SubmitField('Add Note')

# Edit-Form class
class EditNoteForm(Form):
    # Note's category:
    category_str_field  = StringField('Category')
    # Note's title:
    title_str_field     = StringField('Title', validators=[DataRequired()])
    # Note's content:
    str_field           = StringField('Note', validators=[DataRequired()])
    # Add note button:
    submit_Button = SubmitField('Edit Note')

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

# User's directory page:
@app.route('/notes/<user_email>/<sorting_mode>', methods = ['GET', 'POST'])
@app.route('/notes/<user_email>', defaults={'sorting_mode' : 'Date'}, methods = ['GET', 'POST'])
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
@login_required
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
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)

    if note.user_id != current_user.id:
        abort(403)

    db.session.delete(note)
    db.session.commit()
    flash("The Private Note was deleted.", "success")
    return redirect(url_for('notes', user_email=current_user.email, sorting_mode='Date'))

if __name__ == '__main__':
    app.run(debug = True)
