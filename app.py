# ===============================================================================================================
# Private Notes Web Application
# ---------------------------------------------------------------------------------------------------------------
# Nikolai Korolkov, University of Central Florida, December 2020.
# ---------------------------------------------------------------------------------------------------------------
# NOTE:
# The source code is partially based on Alexander Putilin's youTube series and implementation.
# Thank you, Alexander, for providing me with opportunity to learn from you!
# The author granted me a written permission to rely on his videos and implementation for educational purposes.
# ===============================================================================================================

from flask import Flask, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_security import Security, SQLAlchemyUserDatastore, login_required, UserMixin, RoleMixin
import os
import psycopg2

app = Flask(__name__)
# Configuring KEYs from env vars:
app.config['SECRET_KEY'] = 'devkey'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
# flask_security configurations:
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_SEND_PASSWORD_CHANGE_EMAIL'] = False
app.config['SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL'] = False
app.config['SECURITY_FLASH_MESSAGES'] = True
# To be changed in Production server!!!!!! :)
app.config['SECURITY_PASSWORD_SALT'] = 'sJ$_MeLa$G9*KVe43@xV'

# Creating a DB instance
db = SQLAlchemy(app)

# Creating a new table for implementing roles
roles_users = db.Table('roles_users', db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

# User class
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

# Role class used for access-control:
class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

# Note class
class Note(db.Model):
    id   = db.Column(db.Integer, primary_key = True)
    text = db.Column(db.String(256), unique = False, nullable = False)
    
    def __init__(self, note):
        self.text = note
    
    def __repr__(self):
        return '<Note %r>' % self.id

# Form class
class NoteForm(Form):
    # Text field:
    str_field  = StringField('Note', validators=[DataRequired()])
    # Add note button:
    submit_Button = SubmitField('Add Note')

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)
db.create_all()
Bootstrap(app)

# Default page:
@app.route('/', methods = ['GET', 'POST'])
def index():
    flash(u'DEBUG MESSAGE', 'error')
    form = NoteForm()
    if form.validate_on_submit():
        # Setting up DB object:
        note = Note(form.str_field.data)
        # Adding a Note to DB:
        db.session.add(note)
        db.session.commit()
    
    notesList = Note.query

    return render_template('index.html', form = form, notesList = notesList)

if __name__ == '__main__':
    app.run(debug = True)
