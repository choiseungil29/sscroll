import random
import string
import hashlib
import urllib
import ujson
import boto3
import base64
import enums

from sqlalchemy import or_, desc

from flask import Flask, url_for, redirect, request, session, make_response, Blueprint, render_template
from bs4 import BeautifulSoup

import db

from datetime import datetime, timedelta
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


@api('/contents', methods=['GET'])
def fill(context):
    print('contents')
    search_range = datetime.utcnow().replace(month=1).replace(day=1).replace(hour=0).replace(minute=0)

    all_data = db.session.query(models.Content).\
        all()

    random.shuffle(all_data)
    
    showed_all = db.session.query(models.ShowedContent).\
        filter(models.ShowedContent.uid == context.user.id).\
        all()

    data = []
    for c in all_data:
        if len(data) > 10:
            break

        if len(list(filter(lambda x: x.cid == c.id, showed_all))) > 0:
            continue

        data.append(c)
    
    return ujson.dumps([c.to_json() for c in data])

@api('/contents/<id>/comments', methods=['GET'])
def comments(context, id):
    content = db.session.query(models.Content).\
        filter(models.Content.permanent_id == id).\
        first()
    
    return ujson.dumps([c.to_json() for c in content.comments])


@api('/contents/<id>/view', methods=['POST'])
def view_content(context, id):
    content = db.session.query(models.Content).\
        filter(models.Content.permanent_id == id).\
        first()

    showed = db.session.query(models.ShowedContent).\
        filter(models.ShowedContent.cid == content.id).\
        filter(models.ShowedContent.uid == context.user.id).\
        first()
    
    if not showed:
        showed = models.ShowedContent(uid=context.user.id, cid=content.id)
        db.session.add(showed)
        db.session.commit()
    return 'view'


@api('/contents/<id>/like', methods=['POST'])
def like_content(id, context):
    content = db.session.query(models.Content).\
        filter(models.Content.permanent_id == id).\
        first()

    if content in context.user.likes:
        context.user.likes.remove(content)
    else:
        context.user.likes += [content]
    db.session.commit()

    return ujson.dumps(content.to_json())


@api('/contents/<id>/unlike', methods=['POST'])
def unlike_content(id, context):
    content = db.session.query(models.Content).\
        filter(models.Content.permanent_id == id).\
        first()

    if content in context.user.unlikes:
        context.user.unlikes.remove(content)
    else:
        context.user.unlikes += [content]
    db.session.commit()

    return ujson.dumps(content.to_json())


@api('/contents/<id>', methods=['GET'])
def get_content(id, context):
    content = db.session.query(models.Content).\
        filter(models.Content.permanent_id == id).\
        first()

    return ujson.dumps(content.to_json())


@api('/comment', methods=['POST'])
def comment(context):
    """
    코멘트를 작성하는 API
    작성 후 맨 아래로 스크롤되어짐
    """

    permanent_id = request.json['content_pid']
    comment_data = request.json['comment']

    content = db.session.query(models.Content).\
        filter(models.Content.permanent_id == permanent_id).\
        first()

    comment = models.Comment(created_at=datetime.now(), uid=context.user.id, data=comment_data, cid=content.id)

    if 'parent_id' in request.json:
        comment.parent_id = request.json['parent_id']
    db.session.add(comment)
    db.session.commit()

    return ujson.dumps(comment.to_json())


@api('/board', methods=['GET'])
def get_boards(context):
    boards = db.session.query(models.Content).\
        filter(models.Content.origin == enums.DataOriginEnum.SSCROLL_BOARD).\
        all()
    
    return ujson.dumps([b.to_json() for b in boards])


@api('/board', methods=['POST'])
def board(context):

    title = request.json['title']
    data = request.json['data']

    m = hashlib.blake2b(digest_size=12)
    m.update((title + str(datetime.utcnow())).encode())
    hashed = m.hexdigest()
    obj = models.Content(title=title, data=data, uid=context.user.id, permanent_id=hashed, origin=enums.DataOriginEnum.SSCROLL_BOARD)
    obj.created_at = datetime.utcnow() + timedelta(hours=9)
    html = BeautifulSoup(obj.data, 'html.parser')
    for img in html.select('img'):
        if img['src'].startswith('data'):
            # process
            data, img_src = img['src'].split(',')
            mime_type = data[5:].split(';')[0]
            type = mime_type.split('/')[1]
            rename = hashlib.sha256(img['alt'].encode()).hexdigest()
            s3.put_object(Body=base64.b64decode(img_src.encode()), Bucket=bucket, Key=f'{rename}.{type}', ACL='public-read')
            img['src'] = Config.CDN_PATH + f'{rename}.{type}'
            del img['alt']
            print(f'upload {rename}.{type}')
            print(f'changed {img["src"]}')
        else:
            # image download
            pass

    obj.data = html.decode()

    db.session.add(obj)
    db.session.commit()

    return ujson.dumps(obj.to_json())


@api('/users', methods=['GET'])
def users(context):
    data = context.user.to_json()

    comments = db.session.query(models.Comment).\
        filter(models.Comment.uid == context.user.id).\
        order_by(models.Comment.created_at.desc()).\
        all()

    data['comments'] = [c.to_json() for c in comments]

    contents = db.session.query(models.Content).\
        filter(models.Content.uid == context.user.id).\
        order_by(models.Content.created_at.desc()).\
        all()
    
    data['contents'] = [c.to_json() for c in contents]

    showed_contents = db.session.query(models.ShowedContent).\
        filter(models.ShowedContent.uid == context.user.id).\
        order_by(models.ShowedContent.updated_at.desc()).\
        all()

    data['recent'] = [s.to_json() for s in showed_contents]

    data['likes'] = [c.to_json() for c in context.user.likes]
    data['unlikes'] = [c.to_json() for c in context.user.unlikes]

    return ujson.dumps(data)