from django.contrib import admin
from .models import FilmWork, Person, Genre


class GenreInline(admin.TabularInline):
    model = FilmWork.genres.through
    extra = 0
    fields = ('genre', )


class PersonInline(admin.TabularInline):
    model = FilmWork.persons.through
    extra = 0


@admin.register(FilmWork)
class FilmWorkAdmin(admin.ModelAdmin):
    list_filter = ('film_type',)
    list_display = ('title', 'imdb_rating')
    fields = (
        'title',
        'description',
        'creation_date',
        'film_type',
        'film_rating',
        'imdb_rating',
    )
    search_fields = ('title', )
    inlines = [
        GenreInline,
        PersonInline,
    ]


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', )
    inlines = [
        PersonInline,
    ]


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    fields = ('genre', 'description')
    list_display = ('genre', )
