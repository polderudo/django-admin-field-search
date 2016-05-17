# -*- coding: utf-8 -*-

from django.contrib.admin.views.main import SEARCH_VAR, PAGE_VAR
from django.template import Library

register = Library()

@register.inclusion_tag('admin/admin_search_fields/admin_search_fields.html')
def admin_search(cl):
    return {
        'cl':cl,
        'search_var': SEARCH_VAR,
        'query_values': cl.model_admin.query_values,
        'admin_search_fields': cl.model_admin.admin_search_fields,
        'page_var' : PAGE_VAR,
    }

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)