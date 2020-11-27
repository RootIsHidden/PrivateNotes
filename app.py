from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class PrivateForm(Form):
    # Text field:
    str_field  = StringField('Note:', validators=[DataRequired()])
    # Add note button:
    submit_Button = SubmitField('Add Note')

# Employing Flask:
app = Flask(__name__)
# Configuring KEY using environment variable:
app.config['SECRET_KEY'] = 'devkey'
Bootstrap(app)

# Default page:
@app.route('/', methods = ['GET', 'POST'])
def index():
    # Instanciating a form:
    form = PrivateForm()
    # Obtaining a string from user:
    submitted_note = 'Your_Private_Data'
    if form.validate_on_submit():
        submitted_note = form.str_field.data

    return render_template('index.html', form = form, submitted_note = submitted_note)

if __name__ == '__main__':
    app.run(debug = True)
