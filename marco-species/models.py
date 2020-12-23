# here is where we initialize our database and provide operations on the data
import random
import pymongo
from bson.objectid import ObjectId

# import the LOCAL app configuration namespace
import config

def db_connect():
    """
    Provide a connection to a Mongo database specified in the app configuration
    config.py contains the configuration variables (somewhat low tech approach)
    But achieves via a PEP 20 inspired namespace.

    The db returned is typically stored in flask 'g' (global) object during
    response/request sequence
    """
    # when we refactor, LOG THIS connection
    client = pymongo.MongoClient(config.databse_client_uri)
    db = client[config.database_name]
    return db

def db_init():
    """DEPRECATED
    used for initial testing. does no damage to call it.
    """
    # touch database and initial collections see if error is triggered
    # this will cause the program to die early
    db = db_connect()
    x = db[config.observations_collection].find()
    y = db[config.notes_collection].find()
    # get an admin user, if none, then we should die.
    admin = db[config.users_collection].find({'is_admin':True})
    if admin is None:
        raise ValueError('No administrator was found in users_collection.  Exiting')

def db_new_admin(email):
    """db_new_admin(email) - declares an email to be an admin"""
    db = db_connect()
    # see if user already exists and update, else create new user
    dkey = {'email':email}
    user = db[config.users_collection].find_one(dkey)
    if user:
        # existing user
        db[config.users_collection].update(dkey, {'$set': {'is_admin':True}})
    else:
        # new admin
        db[config.users_collection].insert_one({'email':email, 'is_admin':True, 'name':''})
    return True

def get_unclassified_captureID(email):
    """get a previously unclassified capture_id and assign to email identifier
    (this is a better approach as it avoids uneccesary todo list collisions and minimizes
    queries to smaller list of items
    )
    1. get todo list associated with this email into "items"
    2. if list is empty, create a new todo list and refresh "items"
    3. return first item of items list (we could also randomize here if it makes sense)
    """
    db = db_connect()
    dkey = {'email':email}
    # see if the user has an existing todo list
    items = db[config.todo_collection].find(dkey)
    if items.count() == 0:
        # no todo items for this user, create a new todolist
        todolist_create(email)
        todolist_cleanup()
        # refresh the items list
        items = db[config.todo_collection].find()
    # return the top item on the list
    return items[0]['captureID']

def get_unclassified_captureID1(email=None):
    """
    (DEPRECATED due to inefficiency - too many searches)
    return an unclassified capture_id
    meant to engage users with more species.
    1. create a query randomly weighted selecting species or empty prediction
    1a. 75% QUERY ALL captureID with species confidence of greater than 65%
    1b. else QUERY ALL captureID with empty prediction (no regard to confidence)
    2. return first UNCLASSIFIED item in list

    (POTENTIAL ISSUE: if multiple people are classifing at the same time, they have
    a great chance of working on the same picture -- this wastes resources)
    """
    db = db_connect()
    if email:
        print("Not implemented")

    if random.random() > 0.25:
        dkey = {'mwePREDTOP':'species', 'mweCONFTOP':{'$gt':0.65}}
    else:
        dkey = {'mwePREDTOP':'empty'}

    caps = db[config.study_collection].find(dkey)
    for x in caps:
        captureID = x.get('captureID')
        if db[config.observations_collection].find_one({'captureID':captureID}) is None:
            return x.get('captureID')
    raise ValueError("We classified all the images!  You've got to be kidding me!!")

def random_sample(collection, sample_size):
    """get a random sample of a collection of a particular size"""
    db = db_connect()
    query = db[collection].find()
    collection_size = query.count()
    sample_collection = []
    for i in range(0, sample_size):
        n = random.randint(0, collection_size)
        this_sample = db[collection].find().skip(n).limit(1).next()
        sample_collection.append(this_sample)
    return sample_collection

def todolist_clear_all():
    """todolist_clear_all() - for admin maintenance, will clear user todo lists.
    please use sparingly.
    """
    db = db_connect()
    db.drop_collection(config.todo_collection)
    return True

def todolist_create(email):
    """create a todolist for a user
    1. query for user associated with email, if not a known user, return None
    2. grab a random sample from the study of "sample_size" todo_items
    3. insert the items into the list, and return it
    NOTE: we will prune the list to remove uninteresting todo_items
    before we present to the user
    """
    sample_size = 100
    db = db_connect()
    # query for user, exit if no user in our known users_collection
    user = db[config.users_collection].find_one({'email':email})
    if user is None:
        return False
    # see if user has a todo list
    user_todo_list = db[config.todo_collection].find({'email':email})
    if user_todo_list.count() == 0:
        # get a random sample of items from the study_collection
        sample_list = random_sample(config.study_collection, sample_size)
        todo_list = []
        for item in sample_list:
            # put into todo list (in a later step, we remove uninteresting/pre-classified)
            todo_item = {'captureID':item['captureID'], 'email':email}
            todo_list.append(todo_item)
            db[config.todo_collection].insert_one(todo_item)
        return todo_list
    print("todo list exists")
    return user_todo_list

def todolist_remove(captureID):
    """remove a todolist collection by single captureID"""
    db = db_connect()
    dkey = {'captureID':captureID}
    todo_query = db[config.todo_collection].find(dkey)
    if todo_query.count() > 0:
        for item in todo_query:
            db[config.todo_collection].delete_one(item)
        return True
    return False

def todolist_create_all():
    """DEPRECATED
    todolist_create_all() - this was used to initialize todolists for all users_collection.
    May safely remove this at a future date as the todolist_create() will gracefully work
    with users who do not previously have a list.
    """
    db = db_connect()
    users = db[config.users_collection].find()
    for user in users:
        email = user['email']
        todo_list = todolist_create(email)
        print(todo_list)

def todolist_fetch(email):
    """fetch an existing todolist query"""
    db = db_connect()
    query = db[config.todo_collection].find({'email':email})
    return query

def todolist_cleanup():
    """todolist_cleanup() - removes uninteresting or already classified capture_id
    from the list.  There might be a slightly better way to do this, but works for now.

    This function calls todolist_remove() each time it finds something that is already classified.
    This might be where we can improve it calling it only once (with a list)
    Over time, performance might errode.
    """
    db = db_connect()
    todo_items = db[config.todo_collection].find()
    remove_todos = []
    for item in todo_items:
        captureID = item['captureID']
        dkey = {'captureID':captureID}
        obs = db[config.observations_collection].find(dkey)
        if obs.count() > 0:
            remove_todos.append(captureID)
            todolist_remove(captureID)
    return remove_todos

if __name__ == '__main__':
    # this main was intended to TEST key model functions
    db_init()
    print("db initialized")
    # todolist_create_all()
    clist = todolist_cleanup()
    print(clist)
    db = db_connect()
    users = db[config.users_collection].find()
    for user in users:
        email = user['email']
        captureID = get_unclassified_captureID(email)
        print(email, captureID)
