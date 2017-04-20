from django.conf.urls import url
from . import views

urlpatterns = [
    url('^report/(?P<name>[\-\w]+)/$', views.report, name='report'),
    #url(r'^$', views.landing, name='pub-landing'),
]
