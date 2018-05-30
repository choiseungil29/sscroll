import random

from flask import Flask, render_template
from flask_cors import CORS

from db import session

from models import Content


app = Flask(__name__)
CORS(app)



@app.route('/')
def index():
    c = random.choice(session.query(Content).all())
    # c.data = c.data.replace('https', 'http').replace('https', 'http')
    return render_template('index.html', title=c.title, data=c.data)
