from flask import Flask, render_template, request, session, redirect,flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import math
from email.message import EmailMessage

with open('config.json', 'r') as c:
    parameters = json.load(c)['params']
app = Flask(__name__)
mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": parameters['gmail-user'],
    "MAIL_PASSWORD": parameters['gmail-password']
}
app.config.update(mail_settings)
mail = Mail(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = parameters['upload_location']
localhost = True

if localhost:

    # configuring our database to our app
    app.config['SQLALCHEMY_DATABASE_URI'] = parameters['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = parameters['prod_uri']

db = SQLAlchemy(app)
# SQLALCHEMY_TRACK_MODIFICATIONS = True

app.secret_key = 'super secret key'


class Contacts(db.Model):
    sno =db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    mes = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    sub_title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(10000), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)
    date = db.Column(db.String(12), nullable=True)


@app.route('/')
def home():
    posts = Posts.query.filter_by().all()
    last = len(posts)
    if last>=3:
        # post_limit = int(parameters['no_of_posts'])
        # posts=posts[(last-3):(last+post_limit) + post_limit]
        posts = posts[(last - 3):(last + 1)]
    else:
        posts=posts[:]
    return render_template('index.html', parameters_json=parameters,posts=posts)


@app.route('/about')
def about():
    posts = Posts.query.filter_by()
    return render_template('about.html', parameters_json=parameters, post=posts)


@app.route('/blog')
def blog():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts) / int(parameters['no_of_posts']))
    # pagination Logic
    page = request.args.get('page')

    if (not str(page).isnumeric()):
        page = 1
    page = int(page)

    # if len(posts)>=parameters['no_of_posts']+1:
    post_limit = int(parameters['no_of_posts'])
    #posts=posts[(page-1)*post_limit:(page-1)*post_limit+post_limit]
    #posts = posts[(last+post_limit)-((page-1)*post_limit):(last+post_limit)-((page-1)*post_limit) + post_limit]
    #posts = posts[post_limit-((page-1)*post_limit):post_limit-((page-1)*post_limit) + post_limit]
    posts=posts[((len(posts)-post_limit)-((page-1)*post_limit)):((len(posts)-post_limit)-((page-1)*post_limit))+post_limit]
    # length of posts - no of posts display - page-1-display post: length of post +1-page-1*display post


    # first page
    if page == 1:
        prev = "#"
        next = "/blog?page=" + str(page + 1)

    # Last
    elif page == last:
        prev = "/blog?page=" + str(page - 1)
        next = "#"



    # middle
    else:

        prev = "/blog?page=" + str(page - 1)
        next = "/blog?page=" + str(page + 1)

    return render_template('blog.html', parameters_json=parameters, post=posts, prev=prev, next=next, page=page,last=last)


@app.route('/services')
def skills():
    posts = Posts.query.filter_by().all()[0:parameters['no_of_posts']]
    return render_template('services.html', parameters_json=parameters, post=posts)


@app.route('/post/<string:post_slug>', methods=['GET'])
def post_route(post_slug):
    posts = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', parameters_json=parameters, post=posts)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # fetching details from contact html file
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone_number')
        message = request.form.get('message')
        entry = Contacts(name=name, email=email, phone_num=phone, mes=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()

        msg = Message(subject="Message from :" + name,
                      sender=email,
                      recipients=[parameters['gmail-user']],
                      body=message + '\n' + email + '\n' + phone)
        msg.html = render_template('email.html',name=name,message=message)
        mail.send(msg)
        flash("Thanks for submitting your details.We will get back to you","success")
    posts = Posts.query.filter_by()
    return render_template('contact.html', parameters_json=parameters, post=posts)


@app.route('/dashboard', methods=['GET', 'POSt'])
def dashboard():
    if 'user' in session and session['user'] == parameters['admin_user_name']:
        posts = Posts.query.all()
        return render_template('dashboard.html', parameters_json=parameters, posts=posts)

    if request.method == 'POST':
        user_name = request.form.get('user_name')
        password = request.form.get('pass')

        if user_name == parameters['admin_user_name'] and password == parameters['admin_password']:
            session['user'] = user_name
            posts = Posts.query.all()
            return render_template('dashboard.html', parameters_json=parameters, posts=posts)

    return render_template('admin.html', parameters_json=parameters)


@app.route('/edit/<string:sno>', methods=['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == parameters['admin_user_name']:

        if request.method == 'POST':
            sno = sno
            title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            image = request.form.get('image')
            date = datetime.now()

            if sno == '0':
                post = Posts(sno=sno, title=title, sub_title=tagline, slug=slug, content=content, img_file=image,
                             date=date)
                db.session.add(post)
                db.session.commit()
            elif sno != '0':
                post = Posts.query.filter_by(sno=sno).first()  # multiple serial number vale post hue toh usme se first lene ka
                post.title = title
                post.sub_title = tagline
                post.slug = slug
                post.content = content
                post.img_file = image
                post.date = date
                db.session.commit()
                redirect('/post/' + post.slug)

        post = Posts.query.filter_by(sno=sno).first()

        return render_template('edit.html', parameters_json=parameters, post=post, sno=sno)
    return render_template('admin.html', parameters_json=parameters)


@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == parameters['admin_user_name']:
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded successfully"


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route('/delete/<string:sno>')
def delete(sno):
    if 'user' in session and session['user'] == parameters['admin_user_name']:
        del_post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(del_post)
        db.session.commit()
        return redirect('/dashboard')

  


app.run(debug=True)
