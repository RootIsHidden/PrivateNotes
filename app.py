from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import os
import psycopg2

app = Flask(__name__)
# Configuring KEY using environment variables:
app.config['SECRET_KEY'] = 'devkey'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

# Form class
class NoteForm(Form):
    # Text field:
    str_field  = StringField('Note', validators=[DataRequired()])
    # Add note button:
    submit_Button = SubmitField('Add Note')

# Note class
class Note(db.Model):
    id   = db.Column(db.Integer, primary_key = True)
    text = db.Column(db.String(256), unique = True, nullable = False)
    
    # def __init__(self, note)
    #     self.text = note
    
    def __repr__(self):
        return '<Note %r>' % self.id

db.create_all()
Bootstrap(app)

# Default page:
@app.route('/', methods = ['GET', 'POST'])
def index():
    form = NoteForm()
    
    if form.validate_on_submit():
        # Setting up DB object:
        note = Note()
        note.text = form.str_field.data
        # Adding a Note to DB:
        db.session.add(note)
        db.session.commit()
    
    notesList = Note.query

    return render_template('index.html', form = form, notesList = notesList)

if __name__ == '__main__':
    app.run(debug = True)
