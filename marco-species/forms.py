from flask_wtf import FlaskForm as Form
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError


class TalkForm(Form):
    notes = TextAreaField('Tell us your thoughts!')
    submit = SubmitField('Save')
    