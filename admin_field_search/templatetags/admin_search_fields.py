# -*- coding: utf-8 -*-

from django.contrib.admin.views.main import SEARCH_VAR, PAGE_VAR
from django.template import Library
from django.conf import settings

register = Library()

@register.inclusion_tag('admin/admin_search_fields/admin_search_fields.html')
def admin_search(cl):
    hide_search = True
    if settings.ADMIN_FIELD_SEARCH_HIDE_INITIAL is not None:
        hide_search = settings.ADMIN_FIELD_SEARCH_HIDE_INITIAL

    return {
        'cl':cl,
        'search_var': SEARCH_VAR,
        'query_values': cl.model_admin.query_values,
        'admin_search_fields': cl.model_admin.admin_search_fields,
        'page_var': PAGE_VAR,
        'hide_search': hide_search
    }

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)