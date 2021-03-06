from django.conf.urls import url

from . import views


urlpatterns = [
    url(
        r'^$',
        views.index,
        name='home'
    ),
    url(
        r'^feed/$',
        views.feed,
        name='feed'
    ),
    url(
        r'^archives/$',
        views.PostListView.as_view(),
        name='post-list'
    ),
    url(
        r'^(?P<slug>[^/]+)/$',
        views.PostDetailView.as_view(),
        name='post-detail'
    )
]
