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

from gluon.contrib.simplejson import dumps
from gluon.html import DIV, SCRIPT, TABLE, URL
from gluon.http import HTTP
from string import Template
import math
import logging


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
    # C0103: *Invalid name "%s" (should match %s)*
    # pylint: disable=C0103
    return JqGrid(environment, table)()


class JqGrid(object):
    """Class representing interface to jqgrid, jquery grid plugin."""

    default_options = {
        'data': {},
        'datatype': 'json',
        'mtype': 'GET',
        'contentType': "application/json; charset=utf-8",
        'rowNum': 30,
        'rowList': [10, 20, 30],
        'sortname': 'id',
        'sortorder': 'desc',
        'viewrecords': True,
        'height': '300px'
        }
    default_nav_edit_options = {} # e.g. {'width': 400, 'editCaption': '*'}
    default_nav_add_options = {} # e.g. {'width': 400, 'addCaption': '+'}
    default_nav_del_options = {} # e.g. {'width': 400, 'caption': '-'}
    default_nav_search_options = {} # e.g. {'width': 400, 'caption': '?'}
    default_nav_view_options = {} # e.g. {'width': 400, 'caption': '='}

    template = '''
        jQuery(document).ready(function(){
          jQuery.extend(jQuery.jgrid.edit, { // for both add and edit
            errorTextFormat: function(data){return data.responseText} // match cud()
          });
          jQuery.extend(jQuery.jgrid.del, {
            errorTextFormat: function(data){return data.responseText} // match cud()
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
        nav_grid_options=None,          # Use {...} to enable crud action(s)
        nav_edit_options={},
        nav_add_options={},
        nav_del_options={},
        nav_search_options={},
        nav_view_options={},
        filter_toolbar_options=None,    # Use {} to enable toolbar searching
        pager_div_id=None,
        list_table_id=None
        ):
        request = environment['request']
        self.table = table
        options = dict(self.default_options)
        if jqgrid_options:
            options.update(jqgrid_options)
        options.setdefault(
                'colModel', [{'name':f, 'index':f} for f in table.fields])
        if not 'colNames' in options:
            options['colNames'] = [table[item['name']].label
                    for item in options['colModel']]
        options.setdefault('url', URL(r=request,
                # No need for URL(..., hmac_hash=...) here,
                # because even tampered url won't get access to other table
                args=['data', table], vars=request.vars))
        if request.args[:2] == ['data', str(table)]:
            environment['response'].view = 'generic.json'
            raise HTTP(200, environment['response'].render(self.data(
                    environment, table, query=query, orderby=orderby,
                    fields=[v.get('name') for v in options['colModel']])))
        options.setdefault('editurl', URL(r=request, args=['cud', table]))
        if request.args[:2] == ['cud', str(table)]:
            raise HTTP(200, self.cud(environment, table))
        options.setdefault('caption', 'Data of %s' % table)
        options['pager'] = self.pager_div_id = pager_div_id or \
                ('jqgrid_pager_%s' % table)
        self.list_table_id = list_table_id or ('jqgrid_list_%s' % table)
        self.basic_options = dumps(options)[1:-1]       # Strip quotation marks
        self.initialize_response_files(environment, self.response_files)
        self.callbacks = ''
        if select_callback_url:
            self.callbacks += '''
                onSelectRow: function(id){
                    window.location.href = '%s'.replace('{id}', id);
                },'''%select_callback_url
        self.extra = ''
        if isinstance(nav_grid_options, dict):
            self.default_nav_edit_options.update(nav_edit_options)
            self.default_nav_add_options.update(nav_add_options)
            self.default_nav_del_options.update(nav_del_options)
            self.default_nav_search_options.update(nav_search_options)
            self.default_nav_view_options.update(nav_view_options)
            self.extra += \
                "jQuery('#%s').jqGrid('navGrid', '#%s', %s, %s,%s,%s,%s,%s);"%(
                self.list_table_id, self.pager_div_id, dumps(nav_grid_options),
                self.default_nav_edit_options, self.default_nav_add_options,
                self.default_nav_del_options, self.default_nav_search_options,
                self.default_nav_view_options)
        if isinstance(filter_toolbar_options, dict):
            self.extra += "jQuery('#%s').jqGrid('filterToolbar',%s);"%(
                    self.list_table_id, dumps(filter_toolbar_options))


    @classmethod # this way we need not bother to build a JqGrid instance first
    def initialize_response_files(cls, environment, response_files=[],
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
        if not response_files: # then use default location
            response_files = [URL(a=appname, c='static', f=x) for x in [
                    'jqueryui/css/%s/jquery-ui.custom.css'%theme,
                    'jqueryui/js/jquery-ui.custom.min.js',
                    'jqgrid/css/ui.jqgrid.css',
                    'jqgrid/js/i18n/grid.locale-%s.js'%(lang or 'en'),
                    'jqgrid/js/jquery.jqGrid.min.js',
                    ]]
        environment['response'].files.extend(response_files)
        return response_files


    def __call__(self):
        return DIV(self.script(), self.list(), self.pager())

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
        rows = []
        page = int(request.vars.page)
        pagesize = int(request.vars.rows)
        limitby = (page * pagesize - pagesize, page * pagesize)
        if not query:
            query = table.id > 0
        for k, v in request.vars.items():
            #Only works when filter_toolbar_options != {stringResult:True, ...}
            if k in table.fields and v:
                if table[k].type in ('text','string'):
                    query = query & table[k].startswith(v)
                elif table[k].type in ('id', 'integer','float','double'):
                    # intentionally not use exact matching
                    query = query & (table[k].like(v+'%')) # startswith() fails
                elif table[k].type.startswith('list:reference'):
                    query = query & (table[k].contains(v))
                elif table[k].type.startswith('reference'):
                    query = query & (table[k]==int(v))
                else:
                    logging.warn('Unsupported %s: %s=%s'%(table[k].type, k, v))
        logging.debug('query = %s'%query)
        if orderby is None:
            assert request.vars.sidx in table, 'VirtualField is not sortable'
            if request.vars.sidx in table:
                orderby = table[request.vars.sidx]
            if orderby and request.vars.sord == 'desc':
                orderby = ~(orderby)
        for r in table._db(query).select(limitby=limitby, orderby=orderby):
            vals = []
            for f in fields or table.fields:
                if (f in table and table[f].represent):
                    vals.append(table[f].represent(r[f]))
                else:
                    vals.append(r[f])
            rows.append(dict(id=r.id, cell=vals))
        logging.debug('SQL = %s'%table._db._lastsql)
        total_records = table._db(query).count()
        total_pages = int(math.ceil(total_records / float(pagesize)))
        return dict(
                total=total_pages,
                page=min(page, total_pages),
                rows=rows,
                records=total_records)

    @classmethod
    def cud(self, environment, table):
        "Create/update/delete callback, defined by editurl option."
        request = environment['request']
        crud = environment['crud'] # Caller must supply a proper crud instance
        if request.vars.oper=='del' and request.vars.id:
            for del_id in request.vars.id.split(','):
                crud.delete(table, del_id)
        elif request.vars.oper in ['edit', 'add'] and request.vars.id:
            for k, v in request.post_vars.items():
                if k in table and table[k].type.startswith('list:'):
                    # translate list value from jqgrid format into web2py format
                    request.post_vars[k] = filter(None, v.split(','))

            # A dirty hack, so this action will do submit for every visit,
            # with little cost of losing double-submit-protection, see here:
            # http://groups.google.com/group/web2py/msg/fa9d5104257d66a6
            crud.environment.session = None

            form = crud.update(table,
                    request.vars.id if request.vars.id!='_empty' else None,
                    formname=None) # another magic
            if form.errors:
                raise HTTP(406,
                    ', '.join('%s:%s'%(k,v) for k,v in form.errors.items()))

    def list(self):
        """Return a HTML table representing jqgrid list."""
        return TABLE(_id=self.list_table_id)

    def pager(self):
        """Return a HTML div representing jqgrid pager."""
        return DIV(_id=self.pager_div_id)

    def script(self):
        """Return a HTML script representing jqgrid javascript."""
        return SCRIPT(Template(self.template).safe_substitute(self.__dict__))
