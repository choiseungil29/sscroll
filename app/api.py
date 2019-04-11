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

'''@api('/view', methods=['GET'])
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


@api('/recent', methods=['GET'])
def recent(context):
    if context.user is None:
        raise

    recents = db.session.query(models.ShowedContent).\
            filter(models.ShowedContent.uid == context.user.id).\
            order_by(desc(models.ShowedContent.created_at)).\
            all()

    return [recent.to_json() for recent in recents]'''


@api('/contents', methods=['GET'])
def fill(context):
    print('contents')
    search_range = datetime.utcnow().replace(month=1).replace(day=1).replace(hour=0).replace(minute=0)

    all_data = db.session.query(models.Content).\
            all()

    data = []
    for d in range(3):
        data.append(random.choice(all_data))
    
    return ujson.dumps([c.to_json() for c in all_data])
    # return ujson.dumps([c.to_json() for c in all_data])

@api('/contents/<id>/comments', methods=['GET'])
def comments(context, id):

    content = db.session.query(models.Content).\
        filter(models.Content.permanent_id == id).\
        first()
    
    return ujson.dumps([c.to_json() for c in content.comments])


@api('/<id>', methods=['GET'])
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

