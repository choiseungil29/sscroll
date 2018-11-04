import random
import hashlib
import urllib
import ujson
import boto3
import base64

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
def index(context):
    search_range = datetime.utcnow().replace(month=1).replace(day=1).replace(hour=0).replace(minute=0)

    all_data = db.session.query(models.Content).\
            filter(models.Content.created_at > search_range).\
            all()

    c = random.choice(all_data)
    m = hashlib.sha256(c.title.encode())
    if c.permanent_id != m.hexdigest():
        db.session.delete(c)
        db.session.commit()
        return redirect(url_for('api.index'))

    res = make_response(redirect(url_for('content', url=c.permanent_id)))
    if context.user is not None:
        # 유저가 존재하면 기록한다.
        showed_content = db.session.query(models.ShowedContent).\
                filter(models.ShowedContent.uid == context.user.id).\
                filter(models.ShowedContent.cid == c.id).\
                first()

        if showed_content is not None:
            return redirect(url_for('api.index'))

        showed_content = models.ShowedContent(uid=context.user.id, content=c)
        db.session.add(showed_content)
    else:
        # 쿠키에 있으면 넘김.
        views = ujson.loads(request.cookies.get('views', ujson.dumps([])))
        is_view = list(filter(lambda x: x['cid'] == c.permanent_id, views))
        if len(is_view) > 0:
            print('already views')
            return redirect(url_for('api.index'))

        views.append({
            'cid': c.permanent_id
        })
        
        res.set_cookie('views', ujson.dumps(views))

    db.session.commit()
    return res

@api('/fill', methods=['GET'])
def fill(context):
    search_range = datetime.utcnow().replace(month=1).replace(day=1).replace(hour=0).replace(minute=0)

    all_data = db.session.query(models.Content).\
            filter(models.Content.created_at > search_range).\
            all()

    count = 10

    contents = []
    for _ in range(count):
        if context.user is None:
            views = ujson.loads(request.cookies.get('views', ujson.dumps([])))
            not_view = True
            content = None
            while not_view:
                content = random.choice(all_data)
                not_view = len(list(filter(lambda x: x['cid'] == content.permanent_id, views))) == 0
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




@api('/board', methods=['POST'])
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

    return 'success'

