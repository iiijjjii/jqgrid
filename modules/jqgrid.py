#!/bin/env python
# -*- coding: utf-8 -*-

"""
jqgrid.py

Modular access to jqgrid, jQuery grid plugin. http://www.trirand.com/blog/


Example of usage:

# Without a view
controller:
    from modules.jqgrid import JqGrid

    def mycontroller()
        return dict(jqgrid=JqGrid(globals(), db.mytable)())

# With a view
controller:
    from modules.jqgrid import JqGrid

    def mycontroller()
        return dict(jqgrid=JqGrid(globals(), db.mytable)())

view:
    {{=jqgrid}}


# Customize jqgrid options
controller:
    from modules.jqgrid import JqGrid

    def mycontroller():
        jqgrid_options = {
            'colNames': ['ID', 'Name', 'Category'],
            'colModel': [
              {'name': 'id', 'index': 'id', 'width': 55},
              {'name': 'name', 'index': 'name'},
              {'name': 'category', 'index': 'category'},
            ],
            'caption': "List of names and categories.",
            'rowNum': 40,
            'rowList': [20, 40, 60],
            }
        return dict(jqgrid=JqGrid(globals(), db.mytable,
            jqgrid_options=jqgrid_options)())


Requirements (by default they come with the JqGrid standalone app):
    jqgrid
        The default implementation expects to find jqgrid installed at
        static/jqgrid

    jQuery-ui
        The default implementation expects to find the following jquery_ui
        files.
        static/jqueryui/css/jquery-ui.custom.css
        static/jqueryui/js/jquery-ui.custom.js

"""

import gluon.contrib.simplejson as json
from gluon.html import DIV, SCRIPT, TABLE, URL
from gluon.http import HTTP
from string import Template
import math
import logging
import re

DEFAULT = '__USE_DEFAULT_SETTING__'

def JQGRID(environment, table):
    """Convenience function so JQGRID works like a native web2py html helper
    Usage in your controller:
        def foo():
            ...
            return {'bar':DIV(
                H1('blah blah'),
                JQGRID(globals(), db.things),
                )}
    """
    return JqGrid(environment, table)()

class Raw(object):
    "Used by JSONEncoderRaw"
    def __init__(self, payload):
        self.payload = payload
    def as_is(self):
        return self.payload

class JSONEncoderRaw(json.JSONEncoder):
    "Raw objects will be encoded as-is. So output might not be strict json."
    PLACEHOLDER_PATTERN = re.compile(r'"__RAW__-?\d+"')
    locker = {}
    def default(self, obj):
        if isinstance(obj, Raw):
            signature = '__RAW__%s' % id(obj)
            self.locker['"%s"' % signature] = obj.as_is()
            return signature
        return json.JSONEncoder.default(self, obj)
    def encode(self, o):
        result = json.JSONEncoder.encode(self, o)
        for placeholder in self.PLACEHOLDER_PATTERN.findall(result):
            result = result.replace(placeholder, self.locker.pop(placeholder))
        return result


class JqGrid(object):
    """Class representing interface to jqgrid, jquery grid plugin."""

    default_jqgrid_options = {
        'data': {},
        'datatype': 'json',
        'mtype': 'GET',
        'contentType': "application/json; charset=utf-8",
        'rowNum': 30,
        'rowList': [10, 20, 30],
        'sortname': 'id',
        'sortorder': 'desc',
        'viewrecords': True,
        'height': '300px',
        }
    default_options = default_jqgrid_options      # for backward compatibility
    default_nav_grid_options = {
        # http://www.trirand.com/jqgridwiki/doku.php?id=wiki:navigator
        'search': False,  # as of 2011-08-03 navGrid Search not implemented
        'add': False, 'edit': False, 'del': False, 'view': False,
        'refresh': False,
        }
    default_nav_edit_options = {}   # e.g. {'width': 400, 'editCaption': '*'}
    default_nav_add_options = {}    # e.g. {'width': 400, 'addCaption': '+'}
    default_nav_del_options = {}    # e.g. {'width': 400, 'caption': '-'}
    default_nav_search_options = {}     # e.g. {'width': 400, 'caption': '?'}
    default_nav_view_options = {}   # e.g. {'width': 400, 'caption': '='}
    default_filter_toolbar_options = None  # None to disable, {...} to enable

    template = '''
        jQuery(document).ready(function(){
          jQuery.extend(jQuery.jgrid.edit, { // for both add and edit
            errorTextFormat: function(data){
                return data.responseText;        // match cud()
            }
          });
          jQuery.extend(jQuery.jgrid.del, {
            errorTextFormat: function(data){
                return data.responseText;        // match cud()
            }
          });
          jQuery("#$list_table_id").jqGrid({
            complete: function(jsondata, stat) {
                if (stat == "success") {
                    jQuery("#$list_table_id").addJSONData(
                        JSON.parse(jsondata.responseText).d);
                }
            },
            $callbacks
            $basic_options
          });
          $extra
        });'''

    response_files = []         # Can be overrided in controller

    def __init__(self,
        environment,
        table,
        query=None,
        orderby=None,
        jqgrid_options=None,
        select_callback_url=None,
        nav_grid_options=DEFAULT,   # Use None to disable, {...} to enable
        nav_edit_options=DEFAULT,
        nav_add_options=DEFAULT,
        nav_del_options=DEFAULT,
        nav_search_options=DEFAULT,
        nav_view_options=DEFAULT,
        filter_toolbar_options=DEFAULT, # Use None to disable, {...} to enable
        pager_div_id=None,
        list_table_id=None
        ):
        request = environment['request']
        self.table = table
        options = dict(self.default_jqgrid_options)
        if jqgrid_options:
            options.update(jqgrid_options)
        options.setdefault(
                'colModel', [{'name':f, 'index':f} for f in table.fields])
        if not 'colNames' in options:
            options['colNames'] = [table[item['name']].label
                    if item['name'] in table else
                    ' '.join(          # to support virtual or arbitrary field
                        word.capitalize() for word in item['name'].split('_'))
                    for item in options['colModel']]

        data_vars = {'w2p_jqgrid_action': 'data', 'w2p_jqgrid_table': table}
        data_vars.update(request.vars)
        options.setdefault('url', URL(r=request,
                # No need for URL(..., hmac_hash=...) here,
                # because even tampered url won't get access to other table
                args=request.args, vars=data_vars))
        if request.vars.get('w2p_jqgrid_action') == 'data' \
                and request.vars.get('w2p_jqgrid_table') == str(table):
            environment['response'].view = 'generic.json'
            raise HTTP(200, environment['response'].render(self.data(
                    environment, table, query=query, orderby=orderby,
                    fields=[v.get('name') for v in options['colModel']])))

        options.setdefault('editurl', URL(r=request, args=request.args,
                vars={'w2p_jqgrid_action': 'cud', 'w2p_jqgrid_table': table}))
        if request.vars.get('w2p_jqgrid_action') == 'cud' \
                and request.vars.get('w2p_jqgrid_table') == str(table):
            raise HTTP(200, self.cud(environment, table))

        options.setdefault('caption', 'Data of %s' % table)
        options['pager'] = self.pager_div_id = pager_div_id or \
                ('jqgrid_pager_%s' % table)
        self.list_table_id = list_table_id or ('jqgrid_list_%s' % table)
        self.jqgrid_options = options
        self.initialize_response_files(environment, self.response_files)
        self.callbacks = ''
        if select_callback_url:
            self.callbacks += '''
                onSelectRow: function(id){
                    window.location.href = '%s'.replace('{id}', id);
                },''' % select_callback_url

        self.nav_grid_options = self.default_nav_grid_options \
                if nav_grid_options==DEFAULT else nav_grid_options
        self.nav_edit_options = self.default_nav_edit_options \
                if nav_edit_options==DEFAULT else nav_edit_options
        self.nav_add_options = self.default_nav_add_options \
                if nav_add_options==DEFAULT else nav_add_options
        self.nav_del_options = self.default_nav_del_options \
                if nav_del_options==DEFAULT else nav_del_options
        self.nav_search_options = self.default_nav_search_options \
                if nav_search_options==DEFAULT else nav_search_options
        self.nav_view_options = self.default_nav_view_options \
                if nav_view_options==DEFAULT else nav_view_options
        self.filter_toolbar_options = self.default_filter_toolbar_options \
                if filter_toolbar_options==DEFAULT else filter_toolbar_options

    @classmethod    # this way a JqGrid instance is not required
    def initialize_response_files(cls, environment, response_files=None,
            lang='en', theme='ui-lightness'):
        """Method for preparing response.files.

        This is a class method because this will be called without a JqGrid
        instance.
        Args:
            environment: dict, should be: globals()
            response_files: should be a list of url, to override the default
            lang: e.g. 'en'. Valid names are those xx in
                  static/jqgrid/js/i18n/grid.locale-xx.js
            theme: e.g. 'smoothness' or 'ui-lightness', etc.
        """
        appname = JqGrid.__module__.split('.')[1]   # Auto detect this app name
        if not response_files:      # then use default location
            response_files = [URL(a=appname, c='static', f=x) for x in [
                    'jqueryui/css/%s/jquery-ui.custom.css' % theme,
                    'jqueryui/js/jquery-ui.custom.min.js',
                    'jqgrid/css/ui.jqgrid.css',
                    'jqgrid/js/i18n/grid.locale-%s.js' % (lang or 'en'),
                    'jqgrid/js/jquery.jqGrid.min.js',
                    ]]
        environment['response'].files.extend(response_files)
        return response_files

    def __call__(self):
        return DIV(self.script(), self.list(), self.pager())

    def column(self, name):
        """Convenience method used to return the colModel column with the
        provided name.

        Example: set the 'date' column width to 100
            jqgrid.column('date')['width'] = 100
        """
        if not self.jqgrid_options:
            return
        if not 'colModel' in self.jqgrid_options:
            return
        try:
            return [x for x in self.jqgrid_options['colModel'] \
                    if x['name'] == name][0]
        except IndexError:
            return

    @classmethod
    def data(cls, environment, table, query=None, orderby=None, fields=None):
        """Method for accessing jqgrid row data.

        This is a class method because this will be called without a JqGrid
        instance.
        Caveat: Don't use request.args within method.
        Args:
            environment: dict, eg: globals()
            table: DAL Table instance
            query: DAL Query instance
            orderby: DAL orderby instance, if None, the orderby is determined
                by the request.vars.sidx and request.vars.sord.
            fields: list of table field names
        """
        request = environment['request']
        page = int(request.vars.page)
        pagesize = int(request.vars.rows)
        limitby = (page * pagesize - pagesize, page * pagesize)
        if not query:
            query = table.id > 0
        for k, v in request.vars.items():
            #Only works when filter_toolbar_options != {stringResult:True, ...}
            if k in table.fields and v:
                try:
                    query = query & cls.filter_query_by_field_type(table[k], v)
                except SyntaxError as err:
                    logging.warn(err)
            else:
                filter_query = cls.filter_query(table._db, k, v)
                if filter_query:
                    query = query & filter_query
        logging.debug('query = %s', query)
        if orderby is None:
            if request.vars.sidx in table:
                orderby = [table[request.vars.sidx]]
            else:
                orderby = cls.orderby_for_column(table, request.vars.sidx)
            if orderby and request.vars.sord == 'desc':
                orderby = [~x for x in orderby]

        rows = cls.data_rows(table, query, orderby, limitby, fields)
        logging.debug('SQL = %s', table._db._lastsql)
        total_records = table._db(query).count()
        total_pages = int(math.ceil(total_records / float(pagesize)))
        return dict(
                total=total_pages,
                page=min(page, total_pages),
                rows=rows,
                records=total_records)

    @staticmethod
    def filter_query_by_field_type(field, value):
        """Return a query for filtering results on field by field type.

        Args:
            field: gluon.dal.Field instance
            value: mixed, the value of the field to filter on

        Returns:
            gluon.dal.Query instance
        """
        if field.type in ('text', 'string'):
            query = field.startswith(value)
        elif field.type in ('id', 'integer', 'float', 'double',
                'date', 'datetime', 'time'):
            # intentionally not use exact matching
            # note: startswith() fails
            query = (field.like(value + '%'))
        elif field.type.startswith('decimal'):
            query = (field.like(value + '%'))
        elif field.type.startswith('list:reference'):
            query = (field.contains(value))
        elif field.type.startswith('reference'):
            query = (field == int(value))
        elif field.type == 'boolean':
            query = (field == value)
        else:
            # FIXME create custom exception
            raise SyntaxError('No filtering support for field type {t}' \
                    % (field.type))
        return query

    @staticmethod
    def filter_query(db, column, value):
        """Return a query for filtering results

        Override this method to provide custom filtering in a subclass. See
        commented sample code below.

        Args:
            db: gluon.dal.Dal instance
            column: string, jqgrid column name
            value: mixed, the value of the field to filter on

        Returns:
            gluon.dal.Query instance
        """
        query = None
        #if column == 'person' and value:
        #   query = db.person.last_name.startswith(value)
        #elif column == 'thing' and value:
        #   ...
        return query

    @staticmethod
    def orderby_for_column(table, column):
        """Return an orderby expression list for suitable for sorting a
        specific column.

        Override this method to provide custom sorting in a subclass. Columns
        with names that do not match a table field name must be handled here
        for column sorting to work. See commented code below for an example.

        Args:
            table: gluon.dal.Table instance
            column: string, jqgrid column name

        Returns:
            list of gluon.dal.Expression instances
        """
        orderby = None
        # if column == 'person':
        #     orderby = [table._db.person.last_name,
        #             table._db.person.first_name]
        # elif column == 'phone':
        #     orderby = [table._db.person.phone]
        # else:
        #     logging.warn('No sorting for column %s' % (column))
        return orderby

    @staticmethod
    def data_rows(table, query, orderby=None, limitby=None, fields=None):
        """Return data rows for the jqgrid.

        Override this method to provide custom data access (eg table joins)
        in a subclass.

        Args:
            table: gluon.dal.Table instance
            query: gluon.dal.Query instance
            orderby: list of gluon.dal.Expressions
            limitby: tuple (offset, limit)
            fields: list of field names, if None, table.fields is used.

        Return:
            list of dicts,
                eg [{'id': id1, 'cell': ['col1', 'col2', 'col3'..]},...]
        """
        rows = []
        for r in table._db(query).select(limitby=limitby, orderby=orderby):
            vals = []
            for f in fields or table.fields:
                if (f in table and table[f].represent):
                    vals.append(table[f].represent(r[f]))
                else:
                    vals.append(r[f])
            rows.append(dict(id=r.id, cell=vals))
        return rows

    @classmethod
    def cud(cls, environment, table):
        "Create/update/delete callback, defined by editurl option."
        request = environment['request']
        crud = environment['crud']    # Caller must supply proper crud instance
        # Redirection will interfere form editing. Turn them off.
        crud.settings.create_next = None
        crud.settings.update_next = None
        crud.settings.delete_next = None
        if request.vars.oper == 'del' and request.vars.id:
            for del_id in request.vars.id.split(','):
                crud.delete(table, del_id)
        elif request.vars.oper in ['edit', 'add'] and request.vars.id:
            for k, v in request.post_vars.items():
                if k in table:
                    # translate value from jqgrid format into web2py format
                    if table[k].type.startswith('list:'):
                        request.post_vars[k] = [x for x in v.split(',') if x]
                    elif table[k].type == 'boolean':
                        request.post_vars[k] = (v == 'on')

            # A dirty hack, so this action will do submit for every visit,
            # with little cost of losing double-submit-protection, see here:
            # http://groups.google.com/group/web2py/msg/fa9d5104257d66a6
            crud.environment.session = None

            form = crud.update(table,
                    request.vars.id if request.vars.id != '_empty' else None,
                    formname=None)      # another magic
            if form.errors:
                raise HTTP(406,
                    ',<br />'.join('%s:%s' % (form.table[k].label, v)
                        for k, v in form.errors.items())
                    )

    def list(self):
        """Return a HTML table representing jqgrid list."""
        return TABLE(_id=self.list_table_id)

    def pager(self):
        """Return a HTML div representing jqgrid pager."""
        return DIV(_id=self.pager_div_id)

    def script(self):
        """Return a HTML script representing jqgrid javascript."""
        # so user has chance for customizing, between __init__() and script()
        self.basic_options = dumps(self.jqgrid_options)[1:-1]    # Strip quotes
        self.extra = ''
        if isinstance(self.nav_grid_options, dict):
            self.extra += \
                "jQuery('#%s').jqGrid('navGrid','#%s',%s,%s,%s,%s,%s,%s);" % (
                self.list_table_id, self.pager_div_id,
                dumps(self.nav_grid_options),
                dumps(self.nav_edit_options),
                dumps(self.nav_add_options),
                dumps(self.nav_del_options),
                dumps(self.nav_search_options),
                dumps(self.nav_view_options)
                )
        if isinstance(self.filter_toolbar_options, dict):
            self.extra += "jQuery('#%s').jqGrid('filterToolbar',%s);" % (
                    self.list_table_id, dumps(self.filter_toolbar_options))
        return SCRIPT(Template(self.template).safe_substitute(self.__dict__))


def dumps(obj, **kwargs):
    """Serialize obj to a JSON string using JSONEncoderRaw

    By using JSONEncoderRaw, the obj can contain javascript functions.
    """
    return json.dumps(obj, cls=JSONEncoderRaw, **kwargs)

