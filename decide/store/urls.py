from django.urls import path, include, re_path
from . import views


urlpatterns = [
    path('', views.StoreView.as_view(), name='store'),
    re_path('^stats/(?P<voting_id>.+)/$', views.StatsView().as_view()),
]
