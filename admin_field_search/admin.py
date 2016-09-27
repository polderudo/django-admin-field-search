# -*- coding: utf-8 -*-

from django.contrib import admin
from django.db.models import Q, Count
from exceptions import Exception
from django.conf import settings
from datetime import datetime
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.views.main import PAGE_VAR, ALL_VAR
from django.http import QueryDict

COUNT_VAR = "b_count"

def construct_search(field_name):
    if field_name.startswith('^'):
        return "%s__istartswith" % field_name[1:]
    elif field_name.startswith('='):
        return "%s__iexact" % field_name[1:]
    elif field_name.startswith('@'):
        return "%s__search" % field_name[1:]
    else:
        return "%s__icontains" % field_name

class AdminQueryTypes(object):
    qt = None
    field_id = None
    field_name = None
    desc = None
    operator = None
    field_id_name = None
    is_set = False
    set_model_name = None
    input_length = None

    def __init__(self, qt, field_id, field_name, desc, operator=None, is_set=False, set_model_name=None, **kwargs):
        self.qt=qt
        self.field_id=field_id
        self.field_name=field_name
        self.desc=desc
        self.operator=operator
        self.field_id_name = 'qs_%s'% field_id
        self.is_set = is_set
        self.set_model_name = set_model_name
        if kwargs.has_key('length'):
            self.input_length = kwargs.get('length')

class AdminFieldsSearch(admin.ModelAdmin):
    change_list_template = 'admin/admin_search_fields/change_list.html'
    query_values = None

    def __init__(self, *a, **k):
        super(AdminFieldsSearch, self).__init__(*a, **k)

    class Media:
        css = {
            'all': ('admin_field_search/css/admin_field_search.css',)
        }

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super(AdminFieldsSearch, self).get_search_results(request, queryset, search_term)

        try:
            if self.query_values and self.query_values.__len__() > 0:
                for key in self.query_values.keys():
                    value = self.query_values[key]
                    config = [l for l in self.admin_search_fields if l.field_id_name==key][0]
                    if config:
                        field = config.field_name
                        search_value = None

                        search_value, operator = self.get_search_value(field, config.qt, value, config.operator)
                        if not search_value is None:
                            op = operator
                            if config.is_set and op:
                                op = "%s__%s"%(config.set_model_name, operator)

                            qs = []

                            if config.qt == 'D' and not operator:
                                #add 2 querysets (for > and <)
                                dt = search_value.replace(hour=23, minute=59, second=59)

                                op_field = config.set_model_name if config.is_set else field
                                op_from = "%s__gte"%op_field
                                op_to = "%s__lte"%op_field

                                qs.append(Q(**{op_from:search_value}))
                                qs.append(Q(**{op_to:dt}))
                            else:
                                if config.qt!='C':
                                    qs.append(Q(**{op:search_value}))
                                else:
                                    #have to filter the queryset directly
                                    queryset = queryset.annotate(b_count=Count(config.field_name)).filter(Q(**{op:search_value}))

                            for q in qs:
                                queryset = queryset.filter(q)

        except Exception as ex:
            if settings.DEBUG:
                raise ex
            else:
                pass

        return queryset, use_distinct

    def get_changelist(self, request, **k):
        '''have to remove custom query fields, as django doesn't like them
        also pagination for 'Show All' must be handled separate
        '''

        self.query_values = self.get_search_values(request.GET)
        g = request.GET.copy()
        if PAGE_VAR in g and int(g[PAGE_VAR])==-1:
            g[ALL_VAR]=u''

        for key in dict((key, value) for key, value in request.GET.iteritems() if (key.startswith('qs_'))):
            g.pop(key)
        request.GET=g

        return ChangeList

    def get_search_value(self, field, type, obj, operator):
        try:
            op=None
            if operator and not type=='C':
                op = "%s__%s"%(field,operator)
            elif operator and type=='C':
                op = "%s__%s"%(COUNT_VAR, operator)

            if type == 'I':
                return  int(obj), op if op else '%s__exact'%field
            elif type == 'F':
                return float(obj), op if op else '%s__exact'%field
            elif type == 'T':
                return obj.lstrip(' ').rstrip(' '), op if op else construct_search(field)
            elif type == 'B':
                if str(obj) == '1' or str(obj).lower() == 'true' or str(obj).lower() == 'ja':
                    return True, op if op else '%s__exact'%field
                else:
                    return False, op if op else '%s__exact'%field
            elif type == 'C':
                return int(obj), op if op else '%s__exact'%COUNT_VAR
            elif type == 'D':
                try:
                    if ':' in obj:
                        dt = datetime.strptime(str(obj), '%d.%m.%Y %H:%M:%S')
                    else:
                        dt = datetime.strptime(str(obj), '%d.%m.%Y')
                except Exception as ex:
                    dt = None
                return dt, op if op else None

        except:
            return None, op

    def get_search_values(self, data):
        return dict((key, value) for key, value in data.iteritems() if
                    (key.startswith('qs_') and data[key]!=None and len(data[key])>0)
        )

    def get_search_fields(self, data):
        return dict((key, value) for key, value in data.GET.iteritems() if (key.startswith('qs_')))