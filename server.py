from os.path import join, splitext, abspath
from flask import Flask, Response
app = Flask(__name__)


### Global Variables
filepath, extension = splitext(__file__)
PAGES = abspath(join(filepath, '..', 'content/pages'))
POSTS = abspath(join(filepath, '..', 'content/posts'))
CACHE = abspath(join(filepath, '..', 'cache'))
STATIC = abspath(join(filepath, '..', 'static'))


### Controllers
@app.route("/")
def GetHome():
    home_page = open(join(CACHE, 'pages/home.html'), 'r').read()
    return home_page


@app.route("/archives/")
def GetArchives():
    archives_page = open(join(CACHE, 'pages/archives.html'), 'r').read()
    return archives_page


@app.route("/projects/")
def GetProjects():
    projects_page = open(join(CACHE, 'pages/projects.html'), 'r').read()
    return projects_page


@app.route("/friends/")
def GetFriends():
    friends_page = open(join(CACHE, 'pages/friends.html'), 'r').read()
    return friends_page


@app.route("/sitemap/")
def GetSiteMap():
    xml = open(join(STATIC, 'sitemap.xml'), 'r').read()
    return Response(xml, mimetype='text/xml')


@app.route("/robots.txt")
def GetRobots():
    robots = open(join(STATIC, 'robots.txt'), 'r').read()
    return Response(robots, mimetype='text')

@app.route("/monty-hall")
def GetMontyHall():
    index = open(join(STATIC, 'MH', 'index.html'), 'r').read()
    return index;


@app.route("/<slug>/")
def GetPost(slug):
    try:
        post = open(join(CACHE, 'posts/' + slug + '.html'), 'r').read()
        return post
    except:
        missing_page = open(join(CACHE, 'pages/404.html'), 'r').read()
        return missing_page


### Init App
if __name__ == "__main__":
    app.run()
