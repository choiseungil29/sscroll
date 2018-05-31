import random

from flask import Flask, render_template, url_for, redirect
from flask_cors import CORS

from db import session

from models import Content


app = Flask(__name__)
CORS(app)



@app.route('/')
def index():
    c = random.choice(session.query(Content).all())
    # c.data = c.data.replace('https', 'http').replace('https', 'http')
    return redirect(url_for('content', url=c.permanent_id))

@app.route('/<url>')
def content(url):
    c = session.query(Content).filter(Content.permanent_id == url).first()
    if c is None:
        return redirect(url_for('index'))

    return render_template('index.html', title=c.title, data=c.data)
