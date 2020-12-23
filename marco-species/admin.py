from flask import Flask, session, url_for, abort, redirect, g, render_template
from flask_admin.contrib.pymongo import ModelView
import config

# adding flask_admin
from flask_admin import Admin, AdminIndexView, expose
from wtforms import form, fields
from markupsafe import Markup

from models import db_connect

def image_link_formatter(view, context, model, name):
    """I built this based on some examples I saw online, flask admin docs are incomplete"""
    # https://blog.sneawo.com/blog/2017/02/10/flask-admin-formatters-examples/
    val = model.get('pathname','')
    
    if val is '':
        dkey = {'captureID':model.get('captureID')}
        ident = g.db.idents.find_one(dkey)
        val = ident.get('pathname','')
    if val is '':
        return Markup(model.get('captureID'))
    
    url = config.image_server + val
    return Markup('<a href="{}" target="_blank">{}</a>'.format(url, model.get('captureID')))

class UserForm(form.Form):
    name = fields.TextField('Name')
    email = fields.TextField('Email')
    is_admin = fields.BooleanField('Is Admin')

class UserView(ModelView):
    column_list = ('name', 'email', 'is_admin')
    form = UserForm

class IdentForm(form.Form):
    captureID = fields.TextField('captureID')
    mwePREDTOP = fields.TextField('mwePREDTOP')
    mweCONFTOP = fields.FloatField('mweCONFTOP')
    mwsPREDTOP = fields.TextField('mwsPREDTOP')
    mwsCONFTOP = fields.FloatField('mwsCONFTOP')
    pathname = fields.TextField('pathname')
    
class IdentView(ModelView):
    can_create = False
    can_edit = False
    can_delete = False

    column_list = ('captureID', 'mwePREDTOP', 'mweCONFTOP',
                   'mwsPREDTOP', 'mwsCONFTOP', 'mwsCOUNT', 'mwsCOUNTCONF')
    column_searchable_list = ['captureID', 'mwsPREDTOP']
    column_formatters = column_formatters = {
        'captureID': image_link_formatter
    }
    form = IdentForm
    
class ObsForm(form.Form):
    email = fields.TextField('Email')
    captureID = fields.TextField('captureID')
    confirm = fields.BooleanField('confirm')
    species = fields.TextField('species')
    count = fields.IntegerField('count')
    date = fields.TextField('date')
    skip = fields.BooleanField('skip')
    
class ObsView(ModelView):
    can_create = False
    column_list = ('email','captureID','confirm','species','count','skip','date')
    column_searchable_list = ['email','species']
    column_formatters = column_formatters = {
        'captureID': image_link_formatter
    }
    form = ObsForm
    
# flask-admin setup
class MyAdminView(AdminIndexView):
    @expose('/')
    def admin_index(self):
        """this allows us to protect the admin interface"""
        current_user = g.get('current_user')
        if current_user and current_user.get('is_admin'):
            # might want to go to an admin landing page, but I'll go to users view.
            return render_template('admin.html')
        abort(403)
        
def initialize(app):
    admin = Admin(app, index_view=MyAdminView())

    # 'db' is PyMongo database object
    db = db_connect()
    admin.add_view(UserView(db[config.users_collection]))
    # might modify to connect the view to multiple season "shards"
    admin.add_view(IdentView(db[config.idents_collection]))
    # observations
    admin.add_view(ObsView(db[config.observations_collection]))
    