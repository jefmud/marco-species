# auth decorator

from flask import session, url_for
from functools import wraps

def glogin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = dict(session).get('profile', None)
        # You would add a check here and usethe user id or something to fetch
        # the other data for that user/check if they exist
        if user:
            return f(*args, **kwargs)
        return 'You are not logged in -- <a href="' + url_for('glogin') + '">click here to login</a>'
    return decorated_function