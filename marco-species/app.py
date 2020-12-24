# app.py
# the main server app
import sys
import logging
from datetime import datetime  as dt
from datetime import timedelta
import config
from bson.objectid import ObjectId

# server parameters
HOST = '0.0.0.0'
PORT = 5000
DEBUG = False

# basic flask imports
from flask import (abort, Flask, flash, g, get_flashed_messages, redirect, render_template, request, session, url_for)

# flask bootstrap
from flask_bootstrap import Bootstrap

# local imports
import forms
import models
import admin


from auth_decorator import glogin_required

app = Flask(__name__)
app.secret_key = config.secret_key
# set up logging
file_handler = logging.FileHandler('app.log')
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)

# set up admin
admin = admin.initialize(app)
# include bootstrap
Bootstrap(app)

# oAuth Setup
from authlib.integrations.flask_client import OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id= config.google_client_id,
    client_secret= config.google_client_secret,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
)


# request handlers
@app.before_request
def before_request():
    """common before request setup"""
    # a database connection is required.
    g.db = models.db_connect()

    # settings for a default UNIDENTIFIED user
    g.current_user = {'email':'', 'is_admin': False, "name":'anonymous', 'is_authenticated':False}

    # get user data to check if current
    # the google mini-profile is stored in the session
    profile = session.get('profile', None)
    if profile:
        email = profile['email']
        # pull info from our users collection
        current_user = g.db[config.users_collection].find_one({'email':email})
        if current_user:
            current_user['is_authenticated'] = True
            # transfer info into global object
            g.current_user = current_user
            g.current_user['name'] = profile['name']
        else:
            # we know the user, but is not authenticated.
            g.current_user['email'] = email
            g.current_user['name'] = profile['name']


@app.after_request
def after_request(response):
    return response

# Regular routes
@app.route('/')
def index():
    """main landing page"""
    data = {'snapshots':0, 'observations':0}
    return render_template('index.html', data=data)


@app.route('/glogin')
def glogin():
    google = oauth.create_client('google')  # create the google oauth client
    #redirect_uri = url_for('authorize', _external=False)
    #redirect_uri = 'http://serengeti.wfunet.wfu.edu/authorize'

    return google.authorize_redirect(config.redirect_uri)

@app.route('/glogout')
def glogout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')

@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')  # create the google oauth client
    token = google.authorize_access_token()  # Access token from google (needed to get user info)
    resp = google.get('userinfo')  # userinfo contains info specificed in the scope
    user_info = resp.json()
    user = oauth.google.userinfo()  # uses openid endpoint to fetch user info
    # Here you use the profile/user data that you got and query your database find/register the user
    # and set ur own data in the session not the profile from google
    session['profile'] = user_info
    session.permanent = True  # make the session permanant so it keeps existing after browser gets closed
    return redirect('/')

@app.route('/admin/actasuser/<email>')
@glogin_required
def actasuser(email):
    """actasuser(email) - allows an admin to act as a particular user temporarily
    it can only be reversed by logging out and logging in again.
    """
    if g.current_user.get('is_admin'):
        new_user = g.db[config.users_collection].find_one({'email':email})
        if new_user is None:
            return f"{email} was not a valid user"
        # change the session data to reflect the new user
        session['profile'] = {'email':email, 'name': 'admin acting as ' + email}
        return "Impersonation user={} success -- <a href='/'>Go Home</a>".format(email)
    abort(403)


@app.route('/_session')
def session_route():
    """session_route() - "hidden" routine to check what is stored in the profile
    """
    profile = session.get('profile')
    if profile:
        return profile
    return "no session info"

@app.route('/google')
@glogin_required
def profile_google():
    """profile_google() - simple diagnostic route making sure google identity is working
    """
    profile = session['profile']
    email = profile['email']
    return "You are: {}".format(email)

@app.route('/profile')
@glogin_required
def profile_user():
    """profile shows summary data for current user
    might want to REFACTOR and improve for non-WFU participants
    """
    dkey = {'email': g.current_user['email']}
    obs = g.db[config.observations_collection].find(dkey).sort('date',-1)
    talk = g.db[config.notes_collection].find(dkey)
    return render_template('profile.html', obs=obs, talk=talk)

@app.route('/profile/<species_name>')
def profile_species(species_id):
    """Show a listing of observations of a particular species by the user"""
    # here is where we would query for individual species classifications
    # which belong to the current user
    return render_template('observe_species.html')

@app.route('/observe_view/<obs_id>')
@glogin_required
def observe_view(obs_id):
    """show an individual observation by DATABASE ID"""
    dkey = {'_id':ObjectId(obs_id)}
    obs = g.db[config.observations_collection].find_one(dkey)
    obs = dict(obs)
    return str(obs)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/image/<captureID>')
def show_image(captureID):
    try:
        data = g.db[config.idents_collection].find({'captureID':captureID})
        image_url = config.image_server + data.get('pathname')
    except:
        return "No image with that captureID"
    return render_template('image.html', image_url=image_url)

@app.route('/species/<name>')
def species(name):
    """show a list of characteristics associated with a species"""
    return "todo"

@app.route('/todo')
@app.route('/todo/<email>')
@glogin_required
def todo_view(email=None):
    if email is None:
        email = g.current_user['email']
    todolist = models.todolist_fetch(email)
    return render_template('todolist.html', todolist=todolist)

@app.route('/leaderboard')
@glogin_required
def leaderboard():
    observations = g.db[config.observations_collection].find()
    observations = list(observations)
    d = {}
    for obs in observations:
        d[obs['email']] = d.get(obs['email'], 0) + 1
    all_time = sorted(d.items(), key=lambda x: x[1], reverse=True)
    seven_days_ago = str( dt.now() - timedelta(days=7) )

    observations = g.db[config.observations_collection].find({'date': {'$gt':seven_days_ago}})
    observations = list(observations)
    d = {}
    for obs in observations:
        d[obs['email']] = d.get(obs['email'], 0) + 1
    this_week = sorted(d.items(), key=lambda x: x[1], reverse=True)

    return render_template('leaderboard.html', all_time=all_time, this_week=this_week)

@app.route('/_observe/agree/<captureID>')
@glogin_required
def _observe_agree(captureID):
    """user agrees with computer"""
    models.todolist_remove(captureID)
    dkey = {
        'email': g.current_user['email'],
        'captureID': captureID,
        'confirm': True,
        'date': str(dt.now())
        }
    g.db[config.observations_collection].insert_one(dkey)
    return redirect(url_for('observe'))

@app.route('/_observe/empty/<captureID>')
@glogin_required
def _observe_empty(captureID):
    """user encountered an empty picture"""
    models.todolist_remove(captureID)
    dkey = {
        'email': g.current_user['email'],
        'captureID': captureID,
        'count': 0,
        'species': 'none',
        'confirm': False,
        'date': str(dt.now())
    }
    g.db[config.observations_collection].insert_one(dkey)
    return redirect(url_for('observe'))

@app.route('/skip/<captureID>')
@glogin_required
def skip(captureID):
    """skip to next captureID"""
    models.todolist_remove(captureID)
    dkey = {
        'email': g.current_user['email'],
        'captureID': captureID,
        }

    obs = g.db[config.observations_collection].find(dkey)

    if obs.count() == 0:
        #  We made 0 observations... so indicate we are skipping this captureID
        dkey['skip'] = True
        dkey['date'] = str(dt.now())
        g.db[config.observations_collection].insert_one(dkey)

    return redirect(url_for('observe'))


@app.route('/observe')
@app.route('/observe/<captureID>', methods=('GET','POST'))
@glogin_required
def observe(captureID=None):
    if captureID is None:
        # observe something that has never been classified before
        captureID = models.get_unclassified_captureID(g.current_user['email'])
        return redirect(url_for('observe', captureID=captureID))

    # get ident or show a 404
    dkey = {'captureID':captureID}
    data = g.db[config.study_collection].find_one(dkey)
    if data is None:
        abort(404)

    talkform = forms.TalkForm()

    # if request method is POST validate/save
    if request.method == 'POST':
        # handle talk first, it is easy/small
        if talkform.validate_on_submit():
            try:
                dkey = {
                    'email': g.current_user['email'],
                    'captureID': captureID,
                    'notes': talkform.notes.data
                }
                g.db[config.notes_collection].insert_one(dkey)
                return redirect(url_for('observe', captureID=captureID))
            except:
                flash("Problems creating snapshot notes", category="danger")
                app.logger.error('problems creating note for user={}, image={}'.format(g.current_user['email'], captureID))

            return redirect(url_for('observe', captureID=captureID))

        name = request.form.get('species', None)
        if name is None:
            # species was NOT specified-- redirect back to top
            return redirect(url_for('observe', captureID=captureID))

        # get count, if not specifed, make it zero
        count = request.form.get('count', 0)
        try:
            count = int(count)
        except:
            count = 0

        #species_dictionary = models.species_dict(species)
        #user_identified_species_id = species_dictionary[name].get('id')
        species = request.form.get('species')

        # save the observation
        try:
            dkey = {
                'email': g.current_user['email'],
                'captureID': captureID,
                'count': count,
                'species': species,
                'confirm': False,
                'date': str(dt.now())
            }
            g.db[config.observations_collection].insert_one(dkey)
            # flash('Observation saved-- species="{}"'.format(name), category='success')
            # keep classifying a possible secondary species or talkform
            return redirect(url_for('observe', captureID=captureID))
        except Exception as e:
            print(e)
            flash('Problems saving observation!', category='danger')
            app.logger.error('problems saving observation user={}, captureID={}, count={}, species={}'.format(
                g.current_user.email,
                captureID,species))

    # get any observations made by the user on the current image
    dkey = {'email': g.current_user.get('email'), 'captureID':captureID}
    obs = g.db[config.observations_collection].find(dkey)
    talk = g.db[config.notes_collection].find(dkey)

    # build the url for our image, this is NOT present in the dataset, but determined off the pathname
    # valid locations are the proxy "http://serengeti.wfunet.wfu.edu" or "http://10.122.251.51:2019"

    data['url'] = config.image_server + data.get('pathname')
    species = config.species
    species[0] = 'none'
    return render_template('observe.html', data=data, species=config.species, obs=obs, talk=talk, talkform=talkform)

@app.route('/show/<capture_id>')
def image_show(capture_id):
    """get data associated with a particular capture_id"""
    return render_template('image.html')

@app.route('/talk/delete/<_id>')
@glogin_required
def talk_delete(_id):
    """talk item delete"""
    dkey = {'_id':ObjectId(_id)}
    item = g.db[config.notes_collection].find_one(dkey)
    captureID = item['captureID']
    if g.current_user['email'] == item['email'] or g.current_user['is_admin']:
        g.db[config.notes_collection].delete_one(dkey)
    else:
        abort(403) # the user is not allowed to delete this talk item
    return redirect( url_for('observe', captureID=captureID))

@app.route('/observe/delete/<_id>')
@glogin_required
def observe_delete(_id):
    """delete a particular observation"""
    dkey = {'_id':ObjectId(_id)}
    observation = g.db[config.observations_collection].find_one(dkey)
    if observation:
        captureID = observation['captureID']
        if observation['email'] == g.current_user['email'] or g.current_user['is_admin']:
            g.db[config.observations_collection].delete_one(dkey)
            return redirect(url_for('observe', captureID=captureID))
        app.logger.warning('failed delete of observation user={}, observation={}'.format(g.current_user['email'], _id))
        abort(403) # the user is not allowed to delete this observation
    abort(404)

@app.route('/_todolist_clear_all')
@glogin_required
def todo_clear():
    """clear all todo lists"""
    if g.current_user.get('is_admin'):
        models.todolist_clear_all()
        return "Cleared todo lists success -- <a href='/'>Go Home</a>"
    else:
        abort(403)

if __name__ == '__main__':
    args = sys.argv
    args.append('--runserver')
    if '--createsuperuser' in args:
        #models.create_superuser()
        app.logger.info('creating admin user initiated')
        print("** superuser created **")
    elif '--updateimages' in args:
        #models.update_images(args)
        print("** image update complete **")
        sys.exit(0)
    elif '--initdatabase' in args:
        app.logger.info('database initialize begin')
        #models.initialize_database()
        app.logger.info('database initialize completed')
        print("** database initialized **")
    elif '--host' in args:
        PORT = args[args.index('--host') + 1]
    elif '--port' in args:
        PORT = int(args[args.index('--port') + 1])
    elif '--paste' in args:
        from paste import httpserver
        app.logger.info('app started host={}, port={}'.format(HOST,PORT))
        httpserver.serve(app, host=HOST, port=PORT)
    elif '--runserver' in args:
        # see settings at the top of the file
        app.logger.info('app started host={}, port={}'.format(HOST,PORT))
        app.run(host=HOST, port=PORT, debug=DEBUG)
    else:
        msg = """
        app.py valid command line options
        --host (default = '0.0.0.0', defines visibility '0.0.0.0' is completely open)
        --port (default = 5000, defines which port server will run on)
        --createsuperuser (allows creation of an administrative user)
        --initdatabase (initializes the database if required)
        --runserver (runs the server on port configured in source code)
        --paste (runs a paste wsgi server on port configured in source code)
        """
        print(msg)
