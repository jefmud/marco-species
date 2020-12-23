from flask import Flask, session, url_for, abort, redirect
from flask_admin.contrib.pymongo import ModelView


app = Flask(__name__)
app.secret_key = 'skyisonfire'

# adding flask_admin
from flask_admin import Admin, AdminIndexView, expose
from wtforms import form, fields
from markupsafe import Markup

from pymongo import MongoClient

#client = MongoClient('mongodb://127.0.0.1:27017')
client = MongoClient('mongodb://microcoder.org:27017')
db = client.sser


def image_link_formatter(view, context, model, name):
    """I built this based on some examples I saw online, flask admin docs are incomplete"""
    # https://blog.sneawo.com/blog/2017/02/10/flask-admin-formatters-examples/
    val = model.get('pathname','')
    url = 'http://serengeti.wfunet.wfu.edu/' + val
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

@app.route('/fields')
def fields():
    rec = db.idents.find_one()
    print(rec)
    return "see console"

@app.route('/login/<user>')
def login(user):
    """a very basic login that one would supply a known user email,
    Will supplement with Google OAuth2 to ensure as an authority
    """
    rec = db.users.find_one({'email':user})
    if rec:
        session['email'] = rec.get('email')
        session['name'] = rec.get('name')
        session['is_admin'] = rec.get('is_admin')
    else:
        session['email'] = None
        session['name'] = None
        session['is_admin'] = False
        
    return f"login attempt by {user}"

@app.route('/')
def index():
    name = session.get('name')
    if name:
        return f"Welcome {name}"
    else:
        return "Hello stranger"
    
# flask-admin setup
class MyAdminView(AdminIndexView):
    @expose('/')
    def admin_index(self):
        """this allows us to protect the admin interface"""
        if session.get('is_admin'):
            # might want to go to an admin landing page, but I'll go to users view.
            return redirect('/admin/usersview/')
        
        abort(403)
        
def init_db():
    if db.users.find_one({'email':'jefmud@gmail.com'}) is None:
        db.users.insert_one({'email':'jefmud@gmail.com', 'name':'The Jester', 'is_admin':True})
        print('initialized')
    else:
        print('database pass')
    
if __name__ == '__main__':
    init_db()
    admin = Admin(app, index_view=MyAdminView())

    # 'db' is PyMongo database object
    admin.add_view(UserView(db['users']))
    admin.add_view(IdentView(db['idents']))
    
    app.run(host='0.0.0.0',port=5000)

