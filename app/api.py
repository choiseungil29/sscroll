import random
import hashlib
import urllib
import ujson

from flask import Flask, url_for, redirect, request, session, make_response, Blueprint
from bs4 import BeautifulSoup

import db

from datetime import datetime
from app import app, models
from decorator import router

blueprint_api = Blueprint('api', __name__, url_prefix='/api')

api = router(blueprint_api)


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




@api('/logout')
def logout(context):

    if 'email' in session and 'signup_type' in session:
        session.pop('email')
        session.pop('signup_type')

    return redirect(url_for('api.index'))


app.register_blueprint(blueprint_api)
