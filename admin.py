#region Imports
from markdown2 import markdown_path
from BeautifulSoup import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from os import listdir, makedirs
from os.path import splitext, join, dirname, exists
from ntpath import basename
from slugify import slugify
from unidecode import unidecode
import datetime, time
from email import utils
import json
import click
import tests
from flask import Flask, Response
#endregion

#region Config Model
class ConfigurationModel:
    def __init__(self, test = False):
        self.root = splitext(__file__)[0]
        self.pages = join(dirname(self.root), 'content', 'pages.json')
        self.posts = join(dirname(self.root), 'content', 'posts')
        self.templates = join(dirname(self.root), 'templates')
        if test:
            test_dir = join(dirname(self.root), 'test_cache')
            if not exists(test_dir):
                makedirs(test_dir)
            self.cache = test_dir
        else:
            cache_dir = join(dirname(self.root), 'cache')
            if not exists(cache_dir):
                makedirs(cache_dir)
            self.cache = cache_dir
        self.static = join(dirname(self.root), 'static')
        self.env = Environment(loader=FileSystemLoader(join(dirname(self.root), 'templates')))
#endregion

#region Server
app = Flask(__name__)
appconfig = ConfigurationModel()
@app.route("/")
def GetHome():
    home_page = open(join(appconfig.cache, 'home.html'), 'r').read()
    return home_page


@app.route("/sitemap.xml")
def GetSiteMap():
    xml = open(join(appconfig.cache, 'sitemap.xml'), 'r').read()
    return Response(xml, mimetype='text/xml')

@app.route("/feed/")
def GetFeed():
    xml = open(join(appconfig.cache, 'feed.xml'), 'r').read()
    return Response(xml, mimetype='text/xml')


@app.route("/robots.txt")
def GetRobots():
    robots = open(join(appconfig.static, 'robots.txt'), 'r').read()
    return Response(robots, mimetype='text')


@app.route("/<slug>/")
def GetPost(slug):
    try:
        post = open(join(appconfig.cache, slug + '.html'), 'r').read()
        return post
    except:
        missing_page = open(join(appconfig.cache, '404.html'), 'r').read()
        return missing_page
#endregion

#region Update
class Post:
    def __init__(self, file):
        html = markdown_path(file)
        soup = BeautifulSoup(html)
        metas = []
        for thing in soup.p:
            if thing != '\n':
                metas.append(thing)

        self.title =metas[0].replace('<!--', '')
        self.link = slugify(self.title)
        self.description = unidecode(metas[1])
        self.date = basename(file).split('.')[0]
        try:
            self.image = metas[2].replace('<!--', '')
        except IndexError:
            self.image = None
        self.body = unidecode(html)
        self.pubDate = utils.formatdate(time.mktime(datetime.datetime.strptime(self.date, '%Y-%m-%d').timetuple())) # Never touching this again.
        self.rssBody = self.body.replace('<', '&lt;').replace('>', '&gt;')


class Thumbnail:
    def __init__(self, title, image, link, subtitle = None, caption = None):
        self.title = title
        self.image = image
        self.subtitle = subtitle
        self.caption = caption
        self.link = link


class Logger:
    def __init__(self, silent):
        self.silent = silent


    def status(self, message):
        if not self.silent:
            print(message)


class CacheWriter:
    def __init__(self, test = False):
        self.config = ConfigurationModel(test)

        # Read in json for page content
        data = json.load(open(self.config.pages))
        self.HeadlineContent = data["Headlines"]
        self.Headlines = []
        self.ProjectContent = data["Projects"]
        self.Projects = []
        self.FriendContent = data["Friends"]
        self.Friends = []
        self.PostFiles = list(reversed(sorted(listdir(self.config.posts))))
        self.Posts = []
        self.Sites = []

        for file in self.PostFiles:
            self.Posts.append(Post(join(self.config.posts, file)))

        for headline in self.HeadlineContent:
            self.Headlines.append(Thumbnail(
                title = headline["title"],
                image = headline["image"],
                caption = headline["caption"],
                link = headline["link"]
            ))

        for project in self.ProjectContent:
            self.Projects.append(Thumbnail(
                title = project["title"],
                subtitle = project["subtitle"],
                image = project["image"],
                caption = project["caption"],
                link = project["link"]
            ))


        for friend in self.FriendContent:
            self.Friends.append(Thumbnail(
                title = friend["title"],
                subtitle = friend["subtitle"],
                image = friend["image"],
                link = friend["link"]
            ))

        for post in self.Posts:
            self.Sites.append('/' + post.link + '/')
        for page in ['', '/archives/', '/friends/', '/projects/']:
            self.Sites.append(page)


    def Write(self, silent):
        log = Logger(silent)

        # Individual Posts
        log.status("Caching Posts")
        template = self.config.env.get_template('post.html')
        for post in self.Posts:
            with open(join(self.config.cache, post.link + '.html'), 'wb') as file:
                file.write(template.render(
                    data = post
                ))
            log.status("    + " + post.link + '.html')

        # Archives
        log.status("Caching Archives")
        template = self.config.env.get_template('archives.html')
        with open(join(self.config.cache, 'archives.html'), 'wb') as file:
            file.write(template.render(
                data = self.Posts
            ))
        log.status("    + archives.html")

        # RSS
        log.status("Caching RSS")
        template = self.config.env.get_template('feed.xml')
        with open(join(self.config.cache, 'feed.xml'), 'wb') as file:
            file.write(template.render(
                data = self.Posts
            ))
        log.status("    + feed.xml")

        # Home
        log.status("Caching Home")
        template = self.config.env.get_template('home.html')
        with open(join(self.config.cache, 'home.html'), 'wb') as file:
            file.write(template.render(
                data = self.Headlines
            ))
        log.status("    + home.html")

        # Projects
        log.status("Caching Project")
        template = self.config.env.get_template('projects.html')
        with open(join(self.config.cache, 'projects.html'), 'wb') as file:
            file.write(template.render(
                data = self.Projects
            ))
        log.status("    + projects.html")


        # Friends
        log.status("Caching Friends")
        template = self.config.env.get_template('friends.html')
        with open(join(self.config.cache, 'friends.html'), 'wb') as file:
            file.write(template.render(
                data = self.Friends
            ))
        log.status("    + friends.html")

        # Sitemap
        log.status("Caching Sitemap")
        template = self.config.env.get_template('sitemap.xml')
        with open(join(self.config.cache, 'sitemap.xml'), 'wb') as file:
            file.write(template.render(
                data = self.Sites
            ))
        log.status("    + sitemap.xml")
#endregion

#region CLI
@click.group()
def cli():
    """
    This is the admin script for my blog.
    """
    pass


@cli.command()
@click.option('--silent', is_flag=True, help="supress output")
def update(silent):
    """
    Refreshes the content cache
    """
    cw = CacheWriter()
    cw.Write(silent)


@cli.command()
@click.option('--debug', is_flag=True, help="local debugging web server")
def server(debug):
    """
    Runs web server
    """
    if debug:
        app.debug = True
    app.run()


@cli.command()
def test():
    """
    Runs unit tests
    """
    tests.run()


@cli.command()
def email():
    """
    Manages the email subscription engine
    """
    pass


cli.add_command(update)
cli.add_command(test)
cli.add_command(email)
if __name__ == '__main__':
    cli()
#endregion
