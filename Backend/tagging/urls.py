from django.urls import path
from . import views

urlpatterns = [
    path('api/tag', views.tag_query, name='tag_query'),  # Endpoint untuk summary + tagging
    path('api/find_similar_titles', views.find_similar_titles, name='find_similar_titles'),
    path('api/player_statistics', views.player_statistics_view, name='player_statistics'), 
    path('api/match_statistics', views.match_statistics_view, name='match_statistics'),
    path('api/match_details', views.match_details_view, name='match_details'),
]
