from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.card_match_game, name='card_match_game'),
    path('update-score/', views.update_score, name='update_score'),
    path('add-words/', views.add_words, name='add_words'),
    path('type-word-game/', views.type_the_word_game, name='type_word_game'),
]
