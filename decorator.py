import hashlib
import random
import string

from flask import session

from app import app, models

import db

from functools import wraps

import cProfile
pr = cProfile.Profile()

def router(application, **kwargs):
    def route(uri, **kwargs):
        def wrapper(fn):
            @wraps(fn)
            def decorator(*args, **kwargs):
                pr.enable()
                context = ApiContext()
                kwargs['context'] = context
                print('hi')
                res = fn(*args, **kwargs)
                nickname = context.user.to_json()
                print(context.user.to_json())
                pr.disable()
                pr.print_stats(sort='time')
                # print(f'length : ')
                return res
            application.add_url_rule(uri, fn.__name__, decorator, **kwargs)
            return decorator

        return wrapper
    return route


class ApiContext:
    def __init__(self):
        self.user = None

        def create_nickname():
            N = 10
            return ''.join(random.choices(string.ascii_uppercase + string.digits, k=N))

        if 'nickname' not in session:
            nickname = hashlib.shake_128(create_nickname().encode()).hexdigest(length=4)
            session['nickname'] = nickname
        
        self.user = db.session.query(models.User).\
            filter(models.User.nickname == session['nickname']).\
            first()
        
        if self.user is None:
            self.user = models.User(nickname=session['nickname'])
            db.session.add(self.user)
            db.session.commit()