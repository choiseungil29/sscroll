import random
import string
import hashlib
import urllib
import ujson
import boto3
import base64
import enums

from sqlalchemy import or_

from flask import Flask, url_for, redirect, request, session, make_response, Blueprint
from bs4 import BeautifulSoup

import db

from datetime import datetime
from app import app, models
from decorator import router

from mimetypes import guess_extension
from urllib.request import urlretrieve
from config import Config

blueprint_api = Blueprint('api', __name__, url_prefix='/api')

api = router(blueprint_api)

s3 = boto3.client('s3', aws_access_key_id=Config.AWS_ACCESS_KEY_ID, aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY)
bucket = 'sichoi-scroll'


@api('/')
def test(context):
    return 'hi!'

@api('/view', methods=['GET'])
def view(context):
    res = make_response()
    pid = request.args.get('pid')
    if context.user is not None:
        content = db.session.query(models.Content).\
                filter(models.Content.permanent_id == pid).\
                first()
        showed_content = db.session.query(models.ShowedContent).\
                filter(models.ShowedContent.uid == context.user.id).\
                filter(models.ShowedContent.cid == content.id).\
                first()
        if showed_content is None:
            showed_content = models.ShowedContent(uid=context.user.id, content=content)
            db.session.add(showed_content)
            db.session.commit()

    return res



@api('/login', methods=['POST'])
def login(context):
    token = request.json['accessToken']
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
    status = 200

    if user is None:
        user = models.User(signup_type=enums.SignupTypeEnum.NAVER, email = res['response']['email'], access_token=token)
        N = 12
        user.nickname = ''.join(random.choices(string.ascii_uppercase + string.digits, k=N))
        db.session.add(user)
        db.session.commit()
        status = 201

    session['email'] = user.email
    session['signup_type'] = user.signup_type.name

    context.user = user

    return ujson.dumps(user.to_json()), status


@api('/fill', methods=['GET'])
def fill(context):
    print('fill')
    search_range = datetime.utcnow().replace(month=1).replace(day=1).replace(hour=0).replace(minute=0)

    all_data = db.session.query(models.Content).\
            filter(models.Content.created_at > search_range).\
            all()

    count = 10

    contents = []
    for _ in range(count):
        if context.user is None:
            views = ujson.loads(request.args.get('views'))['views']
            not_view = True
            content = None
            while not_view:
                content = random.choice(all_data)
                not_view = len(list(filter(lambda x: x == content.permanent_id, views))) != 0

            contents.append(content)
            all_data.remove(content)
        else:
            not_view = True
            content = None
            while not_view:
                content = random.choice(all_data)
                showed_content = db.session.query(models.ShowedContent).\
                        filter(models.ShowedContent.uid == context.user.id).\
                        filter(models.ShowedContent.cid == content.id).\
                        first()
                not_view = showed_content is not None
            contents.append(content)
            all_data.remove(content)
    
    return ujson.dumps([c.to_json() for c in contents])

        
@api('/<id>', methods=['GET'])
def get_content(id, context):
    content = db.session.query(models.Content).\
            filter(models.Content.permanent_id == id).\
            first()

    return ujson.dumps(content.to_json())
    

@api('/<url>/ward', methods=['POST'])
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



@api('/comment', methods=['POST'])
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


@api('/board', methods=['GET'])
def get_all_board(context):
    boards = db.session.query(models.Board).\
            all()

    return ujson.dumps([b.to_json() for b in boards])

@api('/signup', methods=['POST'])
def signup(context):
    print(request.data)
    req = request.json
    
    user = db.session.query(models.User).\
            filter(models.User.nickname == req['nickname']).\
            first()

    if user is not None:
        return 'EXIST', 400

    context.user.nickname = req['nickname']
    db.session.commit()
    return 'OK'


'''@api('/board', methods=['POST'])
def board(context):

    title = request.form['title']
    content = request.form['content']
    obj = models.Board(title=title, data=content, uid=context.user.id)
    html = BeautifulSoup(obj.data, 'html.parser')
    for img in html.select('img'):
        if img['src'].startswith('data'):
            # process
            data, img_src = img['src'].split(',')
            mime_type = data[5:].split(';')[0]
            type = mime_type.split('/')[1]
            rename = hashlib.sha256(img['data-filename'].encode()).hexdigest()
            s3.put_object(Body=base64.b64decode(img_src.encode()), Bucket=bucket, Key=f'{rename}.{type}', ACL='public-read')
            img['src'] = Config.CDN_PATH + f'{rename}.{type}'
            del img['data-filename']
            del img['style']
            print(f'upload {rename}.{type}')
            print(f'changed {img["src"]}')
        else:
            # image download
            pass

    obj.data = html.decode()

    db.session.add(obj)
    db.session.commit()

    return 'success'''

