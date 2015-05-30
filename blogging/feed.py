import PyRSS2Gen
from .models import Post
import datetime


class RSSFeed:
    def __init__(self):
        items = []
        for post in Post.objects.filter(published=True):
            items.append(PyRSS2Gen.RSSItem(
                title = post.title,
                link = 'http://alexrecker.com/{0}'.format(post.slug),
                description = post.description,
                guid = PyRSS2Gen.Guid('http://alexrecker.com/{0}'.format(post.slug)),
                pubDate=datetime.datetime.strptime(str(post.date), '%Y-%m-%d'),
                author = "alex@reckerfamily.com (Alex Recker)"
            ))

        self.feed = PyRSS2Gen.RSS2(
            title = "Blog by Alex Recker",
            link = "http://alexrecker.com",
            description = "Hey - my name is Alex Recker.  I like to write words.",
            image = PyRSS2Gen.Image(url='http://media.alexrecker.com/images/portrait.jpg', title='Blog by Alex Recker', link='http://alexrecker.com'),
            items = items,
            managingEditor="alex@reckerfamily.com (Alex Recker)"
        )


    def write(self, encoding = "iso-8859-1"):
        try:
            import cStringIO as StringIO
        except ImportError:
            import StringIO
        f = StringIO.StringIO()
        self.feed.write_xml(f, encoding)
        return f.getvalue()