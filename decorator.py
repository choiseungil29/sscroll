
from flask import session

from app import app

import models
import db

from functools import wraps


def route(uri, **kwargs):

    def wrapper(fn):

        @wraps(fn)
        def decorator(*args, **kwargs):
            context = ApiContext()
            kwargs['context'] = context
            return fn(*args, **kwargs)
        app.add_url_rule(uri, fn.__name__, decorator, **kwargs)
        return decorator

    return wrapper


class ApiContext:

    def __init__(self):
        self.user = None

        if 'email' in session and 'signup_type' in session:
            email = session['email']
            signup_type = session['signup_type']

            self.user = db.session.query(models.User).\
                    filter(models.User.email == email).\
                    filter(models.User.signup_type == signup_type).\
                    first()
