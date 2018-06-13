import random
import hashlib
import urllib

from flask import Flask, render_template, url_for, redirect, request
from flask_cors import CORS
from bs4 import BeautifulSoup

from db import session

from models import Content


app = Flask(__name__)


@app.route('/')
def index():
    all_data = session.query(Content).all()
    c = random.choice(all_data)
    m = hashlib.sha256(c.title.encode())
    if c.permanent_id != m.hexdigest():
        session.delete(c)
        session.commit()
        return redirect(url_for('index'))
    return redirect(url_for('content', url=c.permanent_id))

@app.route('/<url>')
def content(url):
    c = session.query(Content).filter(Content.permanent_id == url).first()
    if c is None:
        return redirect(url_for('index'))

    data = BeautifulSoup(c.data, 'html.parser')

    for p in data.select('p'):
        p['style'] = None

    for span in data.select('span'):
        span['style'] = None

    for table in data.select('table'):
        table['style'] = None
    
    for img in data.select('img'):
        if 'height' in img.attrs:
            del img['height']

        if 'width' in img.attrs:
            del img['width']

        img['background-size'] = 'contain'

    data = data.decode()
    session.commit()

    return render_template('index.html', title=c.title, data=data, created_at=c.created_at)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        token = request.form['accessToken']
        header = 'Bearer ' + token
        url = "https://openapi.naver.com/v1/nid/me"
        req = urllib.request.Request(url)
        req.add_header("Authorization", header)
        response = urllib.request.urlopen(req)
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read()
            print(response_body.decode('utf-8'))
        else:
            print("Error Code:" + rescode)
        print('sibal')
        return redirect(url_for('index'))
