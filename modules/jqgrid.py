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

    template = '''
        jQuery(document).ready(function(){
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
          jQuery("#$list_table_id").jqGrid('navGrid', '#$pager_div_id',
            {search: false, add: false, edit: false, del: false});
        });'''

    response_files = []         # Can be overrided in controller

    def __init__(self,
        environment,
        table,
        query=None,
        orderby=None,
        jqgrid_options=None,
        select_callback_url=None,
        pager_div_id=None,
        list_table_id=None
        ):
        self.table = table
        options = dict(self.default_options)
        if jqgrid_options:
            options.update(jqgrid_options)
        options.setdefault('colModel', [{'name':f} for f in table.fields])
        if not 'colNames' in options:
            options['colNames'] = [table[item['name']].label
                    for item in options['colModel']]
        options.setdefault('url', URL(r=environment['request'],
                args=['data', table], vars=environment['request'].vars))
        if environment['request'].args(0) == 'data' and \
                environment['request'].args(1) == str(table):
            environment['response'].view = 'generic.json'
            raise HTTP(200, environment['response'].render(self.data(
                    environment, table, query=query, orderby=orderby,
                    fields=[v.get('name') for v in options['colModel']])))
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
                },''' % select_callback_url

    @classmethod
    def initialize_response_files(cls, environment, response_files=None):
        """Append necessary files to response.files.

        Args:
            environment, eg globals()
            response_files, list of urls of files

        Example:
            # In controller:
            JqGrid.initialize_response_files(globals())
        """
        appname = JqGrid.__module__.split('.')[1]   # Auto detect this app name
        if not response_files:
            response_files = [URL(a=appname, c='static', f=x) for x in [
                    'jqueryui/css/smoothness/jquery-ui.custom.css',
                    'jqueryui/js/jquery-ui.custom.min.js',
                    'jqgrid/css/ui.jqgrid.css',
                    'jqgrid/js/i18n/grid.locale-en.js',
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
            orderby: DAL orderby instance
            fields: list of table field names
        """
        # W0212: *Access to a protected member %s of a client class*
        # pylint: disable=W0212
        request = environment['request']
        rows = []
        page = int(request.vars.page)
        pagesize = int(request.vars.rows)
        limitby = (page * pagesize - pagesize, page * pagesize)
        if not query:
            query = table.id > 0
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
        total_records = table._db(query).count()
        total_pages = int(math.ceil(total_records / float(pagesize)))
        return dict(
                total=total_pages,
                page=min(page, total_pages),
                rows=rows,
                records=total_records)

    def list(self):
        """Return a HTML table representing jqgrid list."""
        return TABLE(_id=self.list_table_id)

    def pager(self):
        """Return a HTML div representing jqgrid pager."""
        return DIV(_id=self.pager_div_id)

    def script(self):
        """Return a HTML script representing jqgrid javascript."""
        return SCRIPT(Template(self.template).safe_substitute(self.__dict__))
