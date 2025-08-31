from django.contrib import admin
from .models import Word

@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    """
    Admin view for the Word model.
    """
    list_display = ('greek_word', 'russian_translation', 'score')
    search_fields = ('greek_word', 'russian_translation')
    list_filter = ('score',)
    ordering = ('score',)