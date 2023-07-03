from flask import Flask, session, render_template, request, redirect, url_for, flash
from functools import wraps
from gallery.tools.db import DbConnection
from ..data.user import User
from ..data.postgres_user_dao import PostgresUserDAO
from werkzeug.utils import secure_filename
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import os
import logging
from gallery.tools.s3 import put_object

app = Flask(__name__)

app.secret_key = os.getenv('FLASK_SESSION_SECRET')

UPLOAD_FOLDER = '/tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_user_dao():
    return PostgresUserDAO()

def check_admin():
    return 'username' in session and session['username'] == 'augrader'

def check_user():
    return 'username' in session

def requires_admin(view):
    @wraps(view)
    def decorated(**kwags):
        if not check_admin():
            return redirect('/login')
        return view(**kwags)
    return decorated

def requires_login(view):
    @wraps(view)
    def decorated(**kwags):
        if not check_user():
            return redirect('/login')
        return view(**kwags)
    return decorated

def upload_to_s3(file):
    try:
        with open(f'/tmp/{file}', 'rb') as data:
            put_object(f'{session["username"]}/{file}', data)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False

@app.route('/')
def home():
    return '''
    <h1>Welcome to the Image Gallery</h1>
    <ul>
        <li><a href="/upload">Upload Image</a></li>
        <li><a href="/view_images">View Images</a></li>
        <li><a href="/admin/users">Admin</a></li>
    </ul
    '''

@app.route('/upload', methods=['GET', 'POST'])
@requires_login
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            if upload_to_s3(filename):
                get_user_dao().insert_image(filename, session['username'])
            return redirect('/')
    return render_template('upload.html')    

@app.route('/view_images')
@requires_login
def view_images():
    s3 = boto3.client('s3')
    images = get_user_dao().get_images_by_owner(session['username'])
    urls = []
    for image in images:
        url = s3.generate_presigned_url('get_object', Params = {'Bucket': os.getenv('S3_IMAGE_BUCKET'), 'Key': image['filename']}, ExpiresIn = 100)
        urls.append(url)
    return render_template('view_images.html', urls=urls)

@app.route('/delete_image/<filename>', methods=['POST'])
@requires_login
def delete_image(filename):
    owner = get_user_dao().get_owner_by_filename(filename)
    if owner != session['username']:
        flash('You do not have permission to delete this image.')
        return redirect(url_for('view_images'))
    s3 = boto3.client('s3')
    try:
        s3.delete_object(Bucket=os.getenv('S3_IMAGE_BUCKET'), Key=f'{session["username"]}/{filename}')
    except ClientError as e:
        logging.error(e)
        flash('Failed to delete image from S3.')
        return redirect(url_for('view_images'))
    get_user_dao().delete_image(filename)
    flash('Image deleted successfully.')
    return redirect(url_for('view_images'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = get_user_dao().get_user_by_username(request.form['username'])
        if user is None or user.password != request.form['password']:
            flash('Invalid username or password')
            return redirect('/login')
        else: 
            session['username'] = request.form['username']
            return redirect('/')
    else:
        return render_template('login.html')

@app.route('/admin/users')
@requires_admin
def admin():
    return render_template('admin.html', users=get_user_dao().get_users())

@app.route('/admin/addUser', methods=['GET', 'POST'])
@requires_admin
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        fullname = request.form['full_name']
        get_user_dao().insert_user(username, password, fullname)
        return redirect('/admin/users')
    return render_template('add_user.html')

@app.route('/admin/editUser/<username>', methods=['GET', 'POST'])
@requires_admin
def edit_user(username):
    if request.method == 'POST':
        new_password = request.form['password']
        new_fullname = request.form['full_name']
        get_user_dao().update_user(username, new_password, new_fullname)
        return redirect('/admin/users')
    user = get_user_dao().get_user_by_username(username)
    return render_template('edit_user.html', user=user)

@app.route('/admin/deleteUser/<username>')
@requires_admin
def delete_user(username):
    get_user_dao().delete_user(username)
    return redirect('/admin/users')

if __name__ == "__main__":
    app.run()
