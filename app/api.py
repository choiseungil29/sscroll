import random
import hashlib
import urllib
import ujson

from flask import Flask, render_template, url_for, redirect, request, session, make_response
from bs4 import BeautifulSoup

import db

import models
import enums

from datetime import datetime
from app import app
from decorator import route


# @app.route('/')
@route('/')
def index(context):
    all_data = db.session.query(models.Content).all()
    c = random.choice(all_data)
    m = hashlib.sha256(c.title.encode())
    if c.permanent_id != m.hexdigest():
        db.session.delete(c)
        db.session.commit()
        return redirect(url_for('index'))

    if context.user is not None:
        # 유저가 존재하면 기록한다.
        showed_content = db.session.query(models.ShowedContent).\
                filter(models.ShowedContent.uid == context.user.id).\
                filter(models.ShowedContent.cid == c.id).\
                first()

        if showed_content is not None:
            return redirect(url_for('index'))

        showed_content = models.ShowedContent(uid=context.user.id, content=c)
        db.session.add(showed_content)

    db.session.commit()
    return redirect(url_for('content', url=c.permanent_id))

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


    comments = filter(lambda x: x.parent_id == None, c.comments)
    comments = sorted(comments, key=lambda x: x.created_at)

    data = data.decode()
    db.session.commit()

    return render_template('content.html', title=c.title, data=data, created_at=c.created_at, user=context.user, comments=comments)


@route('/<url>/ward', methods=['POST'])
def set_ward(url, context):
    c = db.session.query(models.Content).\
            filter(models.Content.permanent_id == url).first()

    res = make_response('와드 성공!')
    if context.user is None:
        wards = ujson.loads(request.cookies.get('wards', ujson.dumps({})))

        if url not in wards:
            ward = models.Ward()
            ward.created_at = datetime.now()
            ward.cid = c.id
            wards[url] = ward.to_json()

        res.set_cookie('wards', ujson.dumps(wards))
    else:
        ward = db.session.query(models.Ward).\
                filter(models.Ward.uid == context.user.id).\
                filter(models.Ward.cid == c.id).\
                first()

        if ward is None:
            ward = models.Ward(uid=context.user.id, cid=c.id)
            db.session.add(ward)

        else:
            res = make_response('이미 와드되어있습니다.')

    db.session.commit()
    return res

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

@route('/comment', methods=['POST'])
def comment(context):
    """
    코멘트를 작성하는 API
    작성 후 맨 아래로 스크롤되어짐
    """
    permanent_id = request.form['permanent_id']
    content = db.session.query(models.Content).\
            filter(models.Content.permanent_id == permanent_id).\
            first()

    comment = models.Comment(created_at=datetime.now(), uid=context.user.id, data=request.form['data'], cid=content.id)
    db.session.add(comment)
    db.session.commit()

    return make_response('댓글 작성 성공')


