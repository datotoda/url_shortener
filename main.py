from flask import Flask, render_template, redirect, url_for, request, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
import time
import string
import random


def get_random_short_url(size=8):
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(size)])


app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'hello'
app.permanent_session_lifetime = timedelta(days=5)

db = SQLAlchemy(app)


class Urls(db.Model):
    _id = db.Column('id', db.Integer, primary_key=True)
    short_url = db.Column(db.String(30))
    url = db.Column(db.String(250))
    viewed = db.Column(db.Integer)
    created = db.Column(db.Integer)
    
    def __init__(self, short_url, url, viewed=0):
        self.short_url = short_url
        self.url = url
        self.viewed = viewed
        self.created = int(time.time())

    def get_id(self):
        return self._id

    def get_url(self):
        return self.url
    
    def get_short_link(self):
        return self.short_url

    def get_short_url(self):
        return url_for('go_to_url', short_link=self.short_url, _external=True)
        
    def get_json(self):
        return {'short_url': self.get_short_url(), 'url': self.url, 'viewed': str(self.viewed), 'created_time': str(self.created)}


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        form_url = request.form.get('form_url', '')
        
        if form_url == '' or len(form_url) > 250:
            flash('input correct url')
            return render_template('index.html', new=True, form_url=form_url)

        short_url = get_random_short_url()
        print(Urls.query.filter_by(short_url=short_url))
        while Urls.query.filter_by(short_url=short_url).first():
            short_url = get_random_short_url()
        
        new_url = Urls(short_url, form_url)
        db.session.add(new_url)
        db.session.commit()
        
        return render_template('index.html', short_url=new_url.get_short_url(), form_url=new_url.url)
    return render_template('index.html', new=True)


@app.route('/premium', methods=['GET', 'POST'])
def premium():
    if request.method == 'POST':
        short_url = request.form.get('premium_short', '')
        form_url = request.form.get('form_url', '')
        
        if any([short_url == '', form_url == '', len(form_url) > 250]):
            flash('input correct urls')
            return render_template('index.html', premium=True, new=True, short_url=short_url, form_url=form_url)

        if Urls.query.filter_by(short_url=short_url).first():
            flash('this short link is already exists')
            return render_template('index.html', premium=True, new=True, form_url=form_url)

        new_url = Urls(short_url, form_url)
        db.session.add(new_url)
        db.session.commit()

        return render_template('index.html', short_url=new_url.get_short_url(), form_url=new_url.url)
    return render_template('index.html', premium=True, new=True)


@app.route('/<short_link>')
def go_to_url(short_link):
    url = Urls.query.filter_by(short_url=short_link).first()
    if url is None:
        return redirect(url_for('home'))
    url.viewed += 1
    db.session.commit()
    return redirect(url.url)


@app.route('/json/all')
def all_json():
    return jsonify({obj.get_id(): obj.get_json() for obj in Urls.query.all()})


@app.route('/old/clear')
def clear():
    delta_time = 2592000  # 30 * 24 * 60 * 60
    changed = False
    for url in Urls.query.filter(Urls.created < int(time.time()) - delta_time).all():
        db.session.delete(url)
        changed = True
    if changed:
        db.session.commit()
    return redirect(url_for('home'))


if __name__ == "__main__":
    db.create_all()
    # app.run(debug=True)
    app.run()
