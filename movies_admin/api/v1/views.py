from django.db.models import QuerySet
from django.http import Http404, JsonResponse
from django.views.generic.list import BaseListView
from django.utils.translation import gettext as _

from movies.models import FilmWork


class MoviesListApi(BaseListView):
    paginate_by = 50
    model = FilmWork
    http_method_names = ['get']  # Список методов, которые реализует обработчик

    def get_queryset(self) -> QuerySet:
        qs = FilmWork.objects.all().values()
        return qs

    def get_context_data(self, *, object_list=None, **kwargs) -> dict:
        qs = self.get_queryset()
        context = self.paginate_queryset(qs, self.paginate_by)
        context['result'] = [result for result in context['result']]
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

    def render_to_response(self, context, **response_kwargs) -> JsonResponse:
        return JsonResponse(context)
