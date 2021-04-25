from django.contrib import admin
from .models import FilmWork, Person, Genre


@admin.register(FilmWork)
class FilmWorkAdmin(admin.ModelAdmin):
    list_display = ('title', 'imdb_rating')


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', )


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('genre', )
