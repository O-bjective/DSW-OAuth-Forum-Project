from flask import Flask, redirect, url_for, session, request, jsonify, Markup
from flask_oauthlib.client import OAuth
from flask import render_template
from bson.objectid import ObjectId

import pymongo
import sys
import dns
import pprint
import os
import json
#os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app = Flask(__name__)

app.debug = True #Change this to False for production

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)

#Set up GitHub as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], #your web app's "username" for github's OAuth
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],#your web app's "password" for github's OAuth
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
    )

#TODO: Create and set a global variable for the name of you JSON file here.  The file will be storedd on Heroku, so you don't need to make it in GitHub

#TODO: Create the file on Heroku using os.system.  Ex) os.system("echo '[]'>"+myFile) puts '[]' into your file


url = 'mongodb+srv://{}:{}@{}/{}'.format(
    os.environ["MONGO_USERNAME"],
    os.environ["MONGO_PASSWORD"],
    os.environ["MONGO_HOST"],
    os.environ["MONGO_DBNAME"]
)
client = pymongo.MongoClient(os.environ["MONGO_HOST"])
db = client[os.environ["MONGO_DBNAME"]]
collection = db['text']
def main():
    url = 'mongodb+srv://{}:{}@{}/{}'.format(
        os.environ["MONGO_USERNAME"],
        os.environ["MONGO_PASSWORD"],
        os.environ["MONGO_HOST"],
        os.environ["MONGO_DBNAME"]
    )
    client = pymongo.MongoClient(url)
    db = client[os.environ["MONGO_DBNAME"]]
    collection = db['message']
        #mongodb+srv://yoitsme:<password>@cluster0-sagjy.mongodb.net/test?retryWrites=true

@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def home():

    allUserNames = "";
    #collection.find_one({})

    for text in collection.find({}):
        vrbl = str(text['_id'])
        allUserNames += "<p>" + text["user"] + ": " + text['message'] + "</p>" + '<form action = "/delete" method = "post"> <button type="submit" name="delete" value="'+vrbl+'">Delete</button> </form>'

    from bson.objectid import ObjectId
    return render_template('home.html', past_posts=Markup(allUserNames))

@app.route('/delete', methods=['POST'])
def delete():
    vrbl2 = request.form["delete"]
    collection.delete_one({"_id": ObjectId(vrbl2)})

    return redirect(url_for("home"))

@app.route('/posted', methods=['POST'])
def post():

    post = {}
    post["user"] = session['user_data']['login']
    post["message"] = request.form["message"]
    collection.insert_one(post)

    return redirect(url_for("home"))
    #This function should add the new post to the JSON file of posts and then render home.html and display the posts.
    #Every post should include the username of the poster and text of the post.

#redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():
        return github.authorize(callback=url_for('authorized', _external=True, _scheme='http')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    return render_template('message.html', message='You were logged out')

@app.route('/login/authorized')
def authorized():
    print("kasa")
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            message='You were successfully logged in as ' + session['user_data']['login']
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.  '
    return render_template('message.html', message=message)

#the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')


if __name__ == '__main__':
    app.run()
