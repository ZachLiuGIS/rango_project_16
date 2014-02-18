from django.conf.urls import patterns, url
from rango import views

urlpatterns = patterns('',
        url(r'^$', views.IndexView.as_view(), name='index'),
        url(r'^about/$', views.about, name='about'),
        url(r'^category/(?P<category_name_url>\w+)/$', views.category, name='category'),
)