import click
import os
import markdown
import codecs
import slugify
import bs4
import time
import datetime
import jinja2
import shutil
import PyRSS2Gen


class Data:
    pass


# Get Paths
ROOT = os.path.dirname(os.path.realpath(__file__))
POSTS = os.path.join(ROOT, 'posts')
TEMPLATES = os.path.join(ROOT, 'templates')
PUBLIC = os.path.join(ROOT, 'public')
STATIC = os.path.join(ROOT, 'static')


class CacheWriter:
    @staticmethod
    def render_html_from_template(template, data):
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATES))
        j_template = env.get_template(template)
        return j_template.render(data = data)


    @staticmethod
    def write_page(template, data, name, path=PUBLIC):
        output = CacheWriter.render_html_from_template(template=template, data=data)
        with open(os.path.join(path, name), 'wb') as file:
            output = bs4.BeautifulSoup(output).prettify()
            file.write(output.encode('utf-8'))


    @staticmethod
    def write_route(template, data, route, root=PUBLIC, test=False, file_override="index.html"):
        path = os.path.join(root, route)
        os.makedirs(path)
        CacheWriter.write_page(template=template, data=data, name=file_override, path=path)


    @staticmethod
    def rebuild_static():
        target = os.path.join(PUBLIC, 'static')
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.copytree(STATIC, target)


    @staticmethod
    def create_feed_route(root=PUBLIC):
        path = os.path.join(root, 'feed')
        os.makedirs(path)


    @staticmethod
    def drop_public(root=PUBLIC):
        """
        Completely purge public folder
        """
        for thing in os.listdir(root):
            try:
                shutil.rmtree(os.path.join(root, thing))
            except:
                os.remove(os.path.join(root, thing))



class Post:
    def __init__(self, path):
        data = self.parse_post_from_file(path)
        self.title = data.title
        self.date = data.date
        self.date_pretty = time.strftime("%B %d, %Y", self.date)
        self.body = data.body
        self.link = data.link
        self.description = data.description
        self.image = data.image


    def __unicode__(self):
        return self.title


    @classmethod
    def parse_post_from_file(cls, path):
        file = codecs.open(path, encoding="utf-8", mode="r")
        contents = file.read()
        file.close()

        md = markdown.Markdown(extensions = ['extra', 'meta'])
        html = md.convert(contents)
        meta = md.Meta

        data = Data()
        data.body = Post.convert_alts_to_captions(html)
        data.title = meta["title"][0]
        data.link = slugify.slugify(data.title)
        data.description = meta["description"][0]
        try:
            data.image = meta["image"][0]
        except KeyError:
            data.image = None
        data.date = time.strptime(meta["date"][0], "%m-%d-%Y")

        return data


    @classmethod
    def convert_alts_to_captions(cls, html):
        soup = bs4.BeautifulSoup(html)
        imgs = soup.find_all('img')
        for tag in imgs:
            src = tag['src']
            try:
                alt = tag['alt']
            except KeyError:
                alt = None
            tag.wrap(soup.new_tag('figure', { 'class': 'image'}))
            tag.parent['class'] = 'image'
            tag.insert_after(soup.new_tag('figcaption'))
            if alt:
                tag.next_sibling.string = alt
        return soup.prettify()


    @staticmethod
    def get_all_posts():
        """
        returns all post objects in order of date desc
        """
        posts = []
        for file in os.listdir(POSTS):
            file = os.path.join(POSTS, file)
            if os.path.isfile(file) and os.path.splitext(file)[1] == '.md':
                posts.append(Post(os.path.abspath(file)))

        return sorted(posts, key=lambda x: x.date, reverse=True)


class RSSFeed:
    def __init__(self, posts):
        items = []
        for post in posts:
            items.append(PyRSS2Gen.RSSItem(
                title = post.title,
                link = "http://alexrecker.com/" + post.link,
                description = post.description,
                guid = PyRSS2Gen.Guid("http://alexrecker.com/" + post.link),
                pubDate = datetime.datetime.fromtimestamp(time.mktime(post.date))
            ))

        self.feed = PyRSS2Gen.RSS2(
            title = "Blog by Alex Recker",
            link = "http://alexrecker.com",
            description = "Hey - my name is Alex Recker.  I like to write words.",
            items = items
        )


    def write(self):
        self.feed.write_xml(open(os.path.join(PUBLIC, 'feed', "index.xml"), "w"))


class WebServer:
    def __init__(self):
        import flask
        self.app = flask.Flask(__name__)
        self.app.debug = True
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/<slug>/', 'slug', self.get_slug)
        self.app.run()


    def index(self):
        return self.read_file('index.html')


    def get_slug(self, slug):
        try:
            return self.read_file(slug)
        except IOError:
            return self.read_file(os.path.join(slug, 'index.html'))


    def read_file(self, target):
        with open(os.path.join(PUBLIC, target)) as file:
            return file.read()


@click.group()
def cli():
    pass


@cli.command(name="refresh")
def cli_refresh():
    """
    regenerate the site html cache
    """
    CacheWriter.drop_public()

    # Posts
    posts = Post.get_all_posts()
    for post in posts:
        CacheWriter.write_route(template="post.html", data=post, route=post.link)

    # Home
    home_data = Data()
    home_data.latest = posts[0]
    home_data.archives = posts
    CacheWriter.write_page(template="home.html", data=home_data, name="index.html")


    # RSS Feed
    CacheWriter.create_feed_route()
    feed = RSSFeed(posts)
    feed.write()


@cli.command(name="serve")
def cli_serve():
    """
    serve site locally
    """
    server = WebServer()


@cli.command(name="deploy")
def cli_deploy():
    """
    sync server's html cache with project's
    """
    pass


@cli.group(name="mail")
def cli_mail():
    """
    manage email subscription engine
    """
    pass


@cli_mail.command(name="list")
def cli_mail_list():
    """
    list current subscribers
    """
    pass


@cli_mail.command(name="add")
def cli_mail_add():
    """
    add a subscriber
    """
    pass


@cli_mail.command(name="remove")
def cli_mail_remove():
    """
    remove a subscriber
    """
    pass


@cli_mail.command(name="latest")
def cli_mail_latest():
    """
    send latest post to subscribers
    """
    pass


if __name__ == '__main__':
    cli()
