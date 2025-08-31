from django.db import models

class Word(models.Model):
    """
    Represents a pair of a Greek word and its Russian translation,
    with a score for tracking learning progress.
    """
    greek_word = models.CharField(max_length=100, unique=True, help_text="The word in Greek")
    russian_translation = models.CharField(max_length=100, help_text="The Russian translation")
    score = models.IntegerField(default=0, help_text="Score for tracking success. +1 for correct, -1 for incorrect.")

    def __str__(self):
        return f"{self.greek_word} - {self.russian_translation}"

    class Meta:
        ordering = ['score'] # Default ordering: show words that need more practice first.
