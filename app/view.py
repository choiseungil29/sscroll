import random
import hashlib
import urllib
import ujson

from flask import Flask, render_template, url_for, redirect, request, session, make_response
from bs4 import BeautifulSoup

import db

import enums

from datetime import datetime
from app import app, models
from decorator import route


@route('/<url>')
def content(url, context):
    c = db.session.query(models.Content).\
            filter(models.Content.permanent_id == url).first()
    if c is None:
        return redirect(url_for('index'))

    data = BeautifulSoup(c.data, 'html.parser')

    for p in data.select('p'):
        del p['style']

    for span in data.select('span'):
        del span['style']

    for table in data.select('table'):
        del table['style']

    for div in data.select('div'):
        if 'class' in div.attrs and 'main' in div.attrs['class'] or 'class' in div.attrs and 'data' in div.attrs['class']:
            continue
        
        del div['style']

    for font in data.select('font'):
        del font['style']
        del font['size']
    
    for img in data.select('img'):
        if 'height' in img.attrs:
            del img['height']

        if 'width' in img.attrs:
            del img['width']

        img['background-size'] = 'contain'

    '''platform = request.user_agent.platform
    if platform == 'android' or platform == 'iphone':
        font_size = '5vw'
    else:
        font_size = '1.5vw' '''

    '''comments = filter(lambda x: x.parent_id == None, c.comments)
    comments = sorted(comments, key=lambda x: x.created_at)'''

    data = data.decode()
    db.session.commit()

    return render_template('content.html', title=c.title, data=data, created_at=c.created_at, user=context.user, comments=[])



@route('/ward')
def ward(context):
    contents = []
    if context.user is None:
        # 비유저의 와드들 가져옴
        wards = ujson.loads(request.cookies.get('wards', ujson.dumps({})))
        contents = db.session.query(models.Content).\
                filter(models.Content.permanent_id.in_([k for k in wards])).\
                all()
    else:
        # 유저의 와드들 가져옴
        wards = db.session.query(models.Ward).\
                filter(models.Ward.uid == context.user.id).\
                all()

        contents = [c.content for c in wards]
    return render_template('ward.html', contents=contents)

@route('/recent')
def recent(context):
    contents = db.session.query(models.ShowedContent).\
            filter(models.ShowedContent.uid == context.user.id).\
            all()

    contents = sorted(contents, key=lambda x: x.created_at)
    contents = contents[::-1]

    return render_template('recent.html', showed_contents=contents)


@route('/login', methods=['GET', 'POST'])
def login(context):
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
            res = ujson.loads(response.read())
        else:
            print("Error Code:" + rescode)

        user = db.session.query(models.User).\
                filter(models.User.email == res['response']['email']).\
                filter(models.User.signup_type == enums.SignupTypeEnum.NAVER).\
                first()

        if user is None:
            user = models.User(signup_type=enums.SignupTypeEnum.NAVER, email = res['response']['email'], access_token=token)
            db.session.add(user)
            db.session.commit()
        else:
            session['email'] = user.email
            session['signup_type'] = user.signup_type.name

        context.user = user
        return redirect(url_for('index'))


@route('/logout')
def logout(context):

    if 'email' in session and 'signup_type' in session:
        session.pop('email')
        session.pop('signup_type')

    return redirect(url_for('index'))



@route('/board/<int:page>')
def board(page, context):
    """
    자유게시판
    """

    PAGE_SIZE = 10

    boards = db.session.query(models.Board).\
            order_by(models.Board.created_at.desc()).\
            limit(PAGE_SIZE).\
            offset((page - 1) * PAGE_SIZE).\
            all()

    return render_template('board_list.html', boards=boards, page=page)

    
    
    
    
    
    
    
    
    
    