import json
import sys
from os.path import splitext, join, dirname
from os import listdir
from slugify import slugify
from BeautifulSoup import BeautifulSoup
from markdown2 import markdown_path
from jinja2 import Environment, FileSystemLoader
from unidecode import unidecode as decode
import datetime
import time
from email import utils


class ConfigurationModel:
    def __init__(self, test = False):
        self.root = splitext(__file__)[0]
        self.pages = join(dirname(self.root), 'content', 'pages.json')
        self.posts = join(dirname(self.root), 'content', 'posts')
        self.templates = join(dirname(self.root), 'templates')
        self.cache = join(dirname(self.root), 'cache')
        self.static = join(dirname(self.root), 'static')
        self.url = 'alexrecker.com'


class Thumbnail:
    def __init__(self, title, image, link, subtitle = None, caption = None):
        self.title = title
        self.image = image
        self.subtitle = subtitle
        self.caption = caption
        self.link = link


class Post:
    def __init__(self, title, date, description, body, image=None):
        self.title = decode(title)
        self.link = decode(slugify(title))
        self.date = date
        self.description = decode(description)
        self.image = image
        self.body = decode(body)
        self.pubDate = utils.formatdate(time.mktime(datetime.datetime.strptime(date, '%Y-%m-%d').timetuple())) # Never touching this again.
        self.rssBody = self.body.replace('<', '&lt;').replace('>', '&gt;')


class SitemapItem:
    def __init__(self, loc, changefreq = 'weekly'):
        self.loc = 'http://' + loc
        self.changefreq = changefreq


class CacheWriter:
    def __init__(self, log = True, full = False, test = False):

        # Get Config Object
        self.config = ConfigurationModel(test)

        # Read in json for page content
        if full:
            data = json.load(open(self.config.pages))
            self.Headlines = data["Headlines"]
            self.Projects = data["Projects"]
            self.Friends = data["Friends"]

        # Read in list of posts
        self.PostFiles = reversed(sorted(listdir(self.config.posts)))
        self.Posts = []

        self.WritePosts(log)
        if full:
            self.WriteHomePage(log)
            self.WriteProjectsPage(log)
            self.WriteFriendsPage(log)


    def WriteHomePage(self, log):
        headlines = []
        for headline in self.Headlines:
            headlines.append(
                Thumbnail(
                    title = headline["title"],
                    image = headline["image"],
                    caption = headline["caption"],
                    link = headline["link"]
                )
            )

        self.WriteOutToTemplate(template_name='home.html', collection=headlines, log = log)


    def WriteProjectsPage(self, log):
        projects = []
        for project in self.Projects:
            projects.append(
                Thumbnail(
                    title = project["title"],
                    subtitle = project["subtitle"],
                    caption = project["caption"],
                    image = project["image"],
                    link = project["link"]
                )
            )

        self.WriteOutToTemplate(template_name='projects.html', collection=projects, log = log)


    def WriteFriendsPage(self, log):
        friends = []
        for friend in self.Friends:
            friends.append(
                Thumbnail(
                    title = friend["title"],
                    subtitle = friend["subtitle"],
                    image = friend["image"],
                    link = friend["link"]
                )
            )

        self.WriteOutToTemplate(template_name='friends.html', collection=friends, log = log)


    def WritePosts(self, log):
        self.Posts = []
        for post in self.PostFiles:
            self.Posts.append(
                self.CreatePost(post)
            )

        # Write to archives
        self.WriteOutToTemplate(template_name='archives.html', collection=self.Posts, log = log)

        # Write out to individual posts
        for post in self.Posts:
            self.WriteOutToTemplate(template_name='post.html', collection=post, post_name = str(post.link) + '.html', log = log)


    def CreatePost(self, post):
        """Creates Post from raw MD"""
        markdown = markdown_path(join(self.config.posts, post))
        raw = BeautifulSoup(markdown)
        metas = []
        for thing in raw.p:
            if thing != '\n':
                metas.append(thing)

        title = metas[0]
        description = metas[1]
        try:
            image = metas[2].string.replace('<!--', '') #TODO: Not sure how this works
        except IndexError:
            image = None # no banner image - that's fine
        body = markdown
        date = post.split('.')[0]

        return Post(
            title = title,
            date = date,
            description = description,
            image = image,
            body = body,
        )


    def UpdateSitemap(self, log):
        collection = []

        # Homepage
        collection.append(SitemapItem(
            loc = self.config.url + '/'
        ))

        # Pages
        for page in ['archives', 'projects', 'friends']: # TODO: Maybe jsonfiy these
            collection.append(SitemapItem(
                loc = self.config.url + '/' + page + '/'
            ))

        # Posts
        for post in self.Posts:
            collection.append(SitemapItem(
                loc = self.config.url + '/' + post.link + '/'
            ))

        self.WriteOutToTemplate('sitemap.xml', collection, log = log)


    def UpdateFeed(self):
        self.WriteOutToTemplate('feed.xml', collection = self.Posts)


    def WriteOutToTemplate(self, template_name, collection, log, post_name=None):
        ENV = Environment(loader=FileSystemLoader(self.config.templates))
        template = ENV.get_template(template_name)

        if post_name is not None:
            template_name = post_name # Writing out to individual post file

        if log:
            print('+ Caching ' + template_name)
        with open(join(self.config.cache, template_name), 'wb') as file:
            file.write(template.render(
                collection = collection
            ))



### Commandline Interface ###
import click
@click.group()
def cli():
    """
        This is the administration script for my blog.
        It handles caching, emails, and testing
    """
    pass


@click.command()
@click.option('--silent', is_flag=True, help="Supress output")
@click.option('--full', is_flag=True, help="Refresh full site")
def update(silent, full):
    """Updates site cache"""
    log = True
    if silent:
        log = False
    writer = CacheWriter(log, full)


@click.command()
def email():
    """Sends and manages email subscriptions"""
    pass


@click.command()
def test():
    """Runs site unit tests"""
    pass


cli.add_command(update)
cli.add_command(email)
cli.add_command(test)


if __name__ == '__main__':
    cli()
