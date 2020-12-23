# config.py
# a configuration namespace for our app

# must have a trailing slash
#image_server = 'http://10.122.251.51:2019/'
image_server = 'http://serengeti.wfunet.wfu.edu/'


# database collections
database_name = "ser"
idents_collection = 'idents'
study_collection = 'study_17_18'
users_collection = 'users'
observations_collection = 'observations'
notes_collection = 'notes'
todo_collection = 'todo'

# be aware--
# key differences in our development vs production server
# for Google redirect requires 127.0.0.1 NOT localhost
# (learned the hard way) trying to use localhost and getting errors
development_server = False
# comes from the user's google console (credentials)
# https://console.cloud.google.com/apis/credentials
if development_server:
    # for development server (127.0.0.1)
    databse_client_uri = 'mongodb://microcoder.org:27017'
    redirect_uri = "http://127.0.0.1:5000/authorize"
    google_client_id = ""
    google_client_secret = ""
else:
    # production server (serengeti.wfunet.wfu.edu)
    databse_client_uri = 'mongodb://127.0.0.1:27017'
    redirect_uri = 'http://serengeti.wfunet.wfu.edu/authorize'
    google_client_id = ""
    google_client_secret = ""

secret_key = 'use-your-secret'

# species from Marco-Willi model
species = [
    'all', 'aardvark', 'aardwolf', 'baboon', 'bat', 'batearedfox', 'buffalo',
    'bushbuck', 'bushpig', 'caracal', 'cattle', 'cheetah', 'civet', 'dikdik',
    'duiker', 'eland', 'elephant', 'fire', 'gazellegrants', 'gazellethomsons',
    'genet', 'giraffe', 'guineafowl', 'hare', 'hartebeest', 'hippopotamus',
    'honeybadger', 'human', 'hyenabrown', 'hyenaspotted', 'hyenastriped',
    'impala', 'insectspider', 'jackal', 'koribustard', 'kudu', 'leopard',
    'lionfemale', 'lionmale', 'mongoose', 'monkeysamango', 'nyala', 'ostrich',
    'otherbird', 'porcupine', 'reedbuck', 'reptiles', 'rhinoceros', 'rodents',
    'sable', 'secretarybird', 'serval', 'steenbok', 'topi', 'vervetmonkey',
    'vulture', 'warthog', 'waterbuck', 'wildcat', 'wilddog', 'wildebeest',
    'zebra', 'zorilla'
]

# kind of wrong to put this in the config, maybe fix refactor later
def species_choices():
    """create tuples for HTML choice controls"""
    ss = []
    for s in species:
        ss.append((s,s))
    return ss

# seasons not currently used in this config-- maybe later
seasons = ['ALL', 'SER_S13', 'SER_S14', 'SER_S15', 'SER_S16']

def select_choices(choice_list):
    """create list of tuples of choices for generic HTML controls"""
    sc = []
    for choice in choice_list:
        sc.append((choice,choice))
    return sc
