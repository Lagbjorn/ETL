from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import F, Q, QuerySet
from django.http import Http404, JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView
from django.utils.translation import gettext as _

from movies.models import FilmWork, PersonJob


class MoviesApiMixin:
    model = FilmWork
    http_method_names = ['get']

    def render_to_response(self, context) -> JsonResponse:
        return JsonResponse(context)

    def get_queryset(self) -> QuerySet:
        # look how we just do it in 2 SQL queries!
        # get queryset for all FilmWorks
        qs = self.model.objects.all().order_by('title').values('id', 'title', 'description', 'creation_date')
        # get queryset for fields with same names as API specification requires
        qs = qs.values('id', 'title', 'description', 'creation_date')
        # add renamed fields; this does not require additional queries to DB
        qs = qs.annotate(rating=F('imdb_rating'))
        qs = qs.annotate(type=F('film_type'))
        # add genres
        qs = qs.annotate(genres=ArrayAgg('genres__genre', distinct=True))
        # add persons
        # could have copy 3 times, but we may extend `job` number later
        for job in PersonJob.values:
            jobs_list = job + 's'  # like actors_list, writers_list and so on
            kwarg = {jobs_list: ArrayAgg('persons__name', distinct=True, filter=Q(filmworkperson__job=job))}
            qs = qs.annotate(**kwarg)
        return qs


class MoviesListApi(MoviesApiMixin, BaseListView):
    paginate_by = 50

    def get_context_data(self, *, object_list=None, **kwargs) -> dict:
        qs = self.get_queryset()
        context = self.paginate_queryset(qs, self.get_paginate_by(qs))
        context = dict(context)
        context['result'] = list(context['result'])
        return context

    def paginate_queryset(self, queryset, page_size) -> dict:
        paginator = self.get_paginator(queryset, page_size)

        page = self.request.GET.get('page', 1)
        try:
            page_num = int(page)
        except ValueError:
            if page == 'last':
                page_num = paginator.num_pages
            else:
                raise Http404(_('Page is not “last”, nor can it be converted to an int.'))

        page = paginator.get_page(page_num)

        # JSON serializer will convert None to null
        prev_page_num = page.previous_page_number() if page.has_previous() else None
        next_page_num = page.next_page_number() if page.has_next() else None

        context = {
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'prev': prev_page_num,
            'next': next_page_num,
            'result': page.object_list,
        }
        return context


class MoviesDetailView(MoviesApiMixin, BaseDetailView):
    pk_url_kwarg = 'id'

    def get_context_data(self, **kwargs):
        context = self.object
        return context
