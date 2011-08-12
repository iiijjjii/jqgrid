# -*- coding: utf-8 -*-
# This file is released under public domain and you can use without limitations
"""
default.py

This controller is used to illustrate usage of the jqgrid module.
"""
import logging
import math

response.menu = [
    ('Minimal', False, URL('minimal'), []),
    ('Customize', False, URL('customize'), []),
    ('Subclass', False, URL('how_to_subclass'), []),
    ('Using View', False, URL('using_a_view'), [
        ('Using View1', False, URL('using_a_view'), []),
        ('Using View2', False, URL('using_a_view_2'), []),
        ]),
    ('Two in One', False, URL('two_in_one'), []),
    ('Components', False, URL('components'), [
        ('Without a View', False, URL('components'), []),
        ('With a View', False, URL('components_with_view'), []),
        ]),
    ('Helper', False, URL('html_helper'), [
        ('Without a View', False, URL('html_helper'), []),
        ('With a View', False, URL('html_helper_with_view'), []),
        ]),
    ('Values as Links', False, URL('as_links'), [
        ('Valid', False, URL('as_links'), []),
        ('Invalid', False, URL('as_links_invalid'), []),
        ]),
    ('Custom Queries', False, URL('custom_query'), [
        ('Custom Query', False, URL('custom_query'), []),
        ('Custom Query 2', False, URL('custom_query_2', args=[1]), []),
        ('Custom Orderby', False, URL('custom_orderby'), []),
        ('Complex Query', False, URL('complex_query', args=[1]), []),
        ]),
    ('Web Service', False, URL('web service'), []),
    ('Callback', False, URL('callback_demo'), []),
    ('Searching', False, URL('toolbar_searching'), [
        ('Toolbar Searching', False, URL('toolbar_searching'), []),
        ]),
    ('Form Editing', False, URL('form_editing'), [
        ('Basic', False, URL('form_editing'), []),
        ('Custom', False, URL('form_editing_custom'), []),
        ]),
    ]

JqGrid = local_import('jqgrid', app='jqgrid', reload=True).JqGrid
JqGrid.initialize_response_files(globals(),     # Better have this explicitly
        # Note: web2py's default base.css conflicts with jQuery-ui 'smoothness'
        # theme.
        theme='ui-lightness',
        lang='en')


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read', 'table name', record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    session.forget()
    return service()


def index():
    """Controller for the default page."""
    response.generic_patterns = ['html']
    return {'': 'Check out demos and their source code, to know how to use'}


def minimal():
    """Create a JqGrid with minimal code.
    No view is necessary. If no view is used the response.generic_patterns
    should be set.
    """
    response.generic_patterns = ['html', 'load']
    return dict(jqgrid=JqGrid(globals(), db.things)())


def customize():
    """Customize jqgrid options.
    http://www.trirand.com/jqgridwiki/doku.php?id=wiki:options
    """
    response.generic_patterns = ['html']
    jqgrid_options = {
        'colNames': ['ID', 'Name', 'Category'],
        'colModel': [
          {'name': 'id', 'index': 'id', 'width': 100},
          {'name': 'name', 'index': 'name', 'width': 200},
          {'name': 'category', 'index': 'category', 'width': 200},
        ],
        'caption': "Custom columns, headings, widths, caption and row numbers.",
        'rowNum': 40,
        'rowList': [20, 40, 60],
        }
    return dict(jqgrid=JqGrid(globals(), db.things,
        jqgrid_options=jqgrid_options)())


def how_to_subclass():
    """Illustrates how to create a subclass.

    A subclass can be used to create a JqGrid with specific features. The
    subclass can then be used throughout a project so all jqgrid tables are
    similar.
    """
    response.generic_patterns = ['html']

    class TalkativeJqgrid(JqGrid):
        """JqGrid subclass that behaves like a JqGrid class with additional
        popups
        """
        # Usually only template is worthy to override
        template = '''
            jQuery(document).ready(function(){
              alert("Ready to init a jqGrid! (Popups courtesy of subclass!)");
              jQuery("#$list_table_id").jqGrid({
                complete: function(jsondata, stat) {
                    if (stat == "success") {
                      var thegrid = jQuery("#$list_table_id")[0];
                      thegrid.addJSONData(JSON.parse(jsondata.responseText).d);
                    }
                },
                $basic_options
              });
              jQuery("#$list_table_id").jqGrid('navGrid', '#$pager_div_id',
                {search: true, add: true, edit: true, del: true}
                );
              alert("jqGrid is loading/loaded!"); // Just a demo
            });'''      # Warn: Make sure you keep those %(...)s intact
        # def data(self): return ...something new... # You might need this too
    jqgrid_options = {'caption': "A talkative JqGrid subclass"}     # optional
    return dict(jqgrid=TalkativeJqgrid(
            globals(), db.category, jqgrid_options=jqgrid_options)())


def using_a_view():
    """Illustrate using a view to display a jqgrid table"""
    # Notice the "()". So, what we transmit into the view, is something
    # similar to a raw string.
    response.generic_patterns = ['load']
    return dict(jqgrid_stuff_but_not_callable=JqGrid(globals(), db.category)())


def using_a_view_2():
    """Illustrate using a view to display a jqgrid table.

    Like using_a_view() except class is called within the view.
    """
    # Get rid of the "()", if you prefer.
    return dict(jqgrid_callable_instance=JqGrid(globals(), db.category))


def two_in_one():
    """Illustrate using two jqgrids on one page.

    Grids can be configured independently by setting options.
    """
    response.generic_patterns = ['html']
    return dict(
        grid1=JqGrid(globals(), db.things,
            jqgrid_options={'width': 540},
            nav_grid_options={'edit': False})(),
        grid2=JqGrid(globals(), db.category,
            jqgrid_options={'caption': "List for grid 2."},
            nav_grid_options={'add': False})())


def components():
    """Illustrates accessing jqgrid tables as a components.

    It is assumed JqGrid.initialize_response_files(globals()) is invoked.
    """
    response.generic_patterns = ['html']
    return dict(blah=DIV(
        H4('Jqgrid displayed with a component!'),
        LOAD(request.controller, 'minimal.load'),
        HR(),
        H4('Even better, multiple JqGrid components appear on the same page!'),
        LOAD(request.controller, 'using_a_view.load',
            # Note that if more than one JqGrid instance appears in same page,
            # each of them should have unique list_table_id and pager_div_id.
            # JqGrid will try to define a unique id for you by default.
            # So in most cases you don't need to worry about that.
            ),
        ))


def components_with_view():
    """Illustrates accessing jqgrid tables as a components.

    Same as components() but using a view.
    """
    return dict()


def html_helper():
    """Illustrates using the modules JQGRID html helper."""
    response.generic_patterns = ['html']
    JQGRID = local_import('jqgrid').JQGRID
    return dict(blah=DIV(
        H4('JQGRID works like a native web2py html helper.'),
        HR(),
        JQGRID(globals(), db.things),
        ))


def html_helper_with_view():
    """Illustrates using the modules JQGRID html helper.

    Same as html_helper() but using a view.
    """
    JQGRID = local_import('jqgrid').JQGRID
    return dict(jqgrid=JQGRID(globals(), db.things))


def as_links():
    """Illustrates converting a column's values to links.

    Predefined format types:
    http://www.trirand.com/jqgridwiki/doku.php?id=wiki:predefined_formatter
    """
    response.generic_patterns = ['html']
    jqgrid_options = {
        'colModel': [
          {'name': 'id', 'index': 'id', 'width': 55},
          {'name': 'name', 'index': 'name'},
          {
            'name': 'category',
            'index': 'category',
            'width': 200,
            'formatter':'showlink',
            'formatoptions':{'baseLinkUrl': 'category'},
          },
        ],
        'caption': "Click category links to see category details."
        }
    return dict(jqgrid=JqGrid(globals(), db.things,
        jqgrid_options=jqgrid_options)())


def as_links_invalid():
    """Illustrates invalid method converting a column's values to links.

    This is the intuitive approach but it doesn't work.
    """
    response.generic_patterns = ['html']
    db.things.name.represent = lambda v: A(v, _href='index')
    # Causes a "JSON serialization error", therefore empty output.
    return dict(jqgrid=JqGrid(globals(), db.things)())


def category():
    """Category CRUD controller.
    Links in as_links() jqgrid category column redirect here.

    Note: The request args and vars are not conventional.
        request.vars.id == id of db.things record (not db.category)
    """
    response.generic_patterns = ['html']
    category_id = 0
    if request.vars.id:
        rows = db(db.things.id == request.vars.id).select()
        if rows:
            category_id = rows[0].category
    form = crud.update(db.category, category_id)
    return dict(form=form)


def custom_query():
    """Illustrates populating jqgrid table with a custom query."""
    response.generic_patterns = ['html']
    return dict(foo=JqGrid(
        globals(),
        db.things,
        query=db.things.price > 500,            # just to illustrate
        jqgrid_options={
            'caption': "Custom query: Only records with price > 500 displayed"
            },
        )())


def custom_query_2():
    """Illustrates populating jqgrid table with a custom query.

    Like custom_query except the query variable is dynamic, obtained from
    request.args(0).
    """
    categories = db(db.category.id > 0).select(limitby=(0,6))
    return dict(categories=categories, jqgrid=JqGrid(
        globals(),
        db.things,
        query=db.things.category==request.args(0),
        jqgrid_options={
            'caption': "Custom query: Click links above to filter by category."
            },
        )())


def custom_orderby():
    """Illustrates sorting jqgrid table with a custom orderby."""
    response.generic_patterns = ['html']
    orderby = None
    if request.vars.sidx == 'price':
        # Customize a compound order
        orderby = db.things.price | db.things.name
        if request.vars.sord == 'desc':
            orderby = ~db.things.price | ~db.things.name
    # Mmm, sorting doesn't work quite well with reference field yet.
    # i.e. "category" in this demo db table
    # if request.vars.sidx == 'category':
    #     orderby = 'things.name'
    #     #if request.vars.sord == 'desc':
    #     #    orderby = ~orderby
    return dict(foo=JqGrid(
        globals(),
        db.things,
        orderby=orderby,
        jqgrid_options={'caption': (
            'Custom orderby: '
            'Click Price column header. '
            'Sorts by price DESC, name DESC'
            )},
        )())


class ComplexJqGrid(JqGrid):

    @classmethod
    def data(cls, environment, table, query=None, orderby=None, fields=None):
        """Method for accessing jqgrid row data.

        # *** Changes from JqGrid method highlighted. ***

        Args:
            See JqGrid data method.
        Returns
            See JqGrid data method.
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
                if table[k].type in ('text', 'string'):
                    query = query & table[k].startswith(v)
                elif table[k].type in ('id', 'integer', 'float', 'double'):
                    # intentionally not use exact matching
                    # note: startswith() fails
                    query = query & (table[k].like(v + '%'))
                elif table[k].type.startswith('list:reference'):
                    query = query & (table[k].contains(v))
                elif table[k].type.startswith('reference'):
                    query = query & (table[k] == int(v))
                else:
                    logging.warn('Unsupported %s: %s=%s', table[k].type, k, v)
        logging.debug('query = %s', query)
        if orderby is None:
            assert request.vars.sidx in table, 'VirtualField is not sortable'
            if request.vars.sidx in table:
                orderby = table[request.vars.sidx]
            if orderby and request.vars.sord == 'desc':
                orderby = ~(orderby)
        # *** Get data using left join ***
        db = table._db
        things = db(query).select(
                db.things.ALL,
                db.category.name,
                left=db.category.on(db.things.category==db.category.id),
                limitby=limitby, orderby=orderby,
                )
        for r in things:
            # The category name is formatted (not very meaningful but
            #   illustrates how it can be done.
            # The things.markup column is a virtual column
            # The reduced column is not found in any table.
            vals = [
                    r.things.name,
                    '* %s *' % (r.category.name.upper()),
                    r.things.cost,
                    r.things.price,
                    r.things.markup,
                    'Reduced' if r.things.price < r.things.cost else '',    # No table column
                    ]
        # ***
            rows.append(dict(id=r.things.id, cell=vals))
        logging.debug('SQL = %s', table._db._lastsql)
        total_records = table._db(query).count()
        total_pages = int(math.ceil(total_records / float(pagesize)))
        return dict(
                total=total_pages,
                page=min(page, total_pages),
                rows=rows,
                records=total_records)

def complex_query():
    """Illustrates displaying jqgrid table a complex query.

    The jqgrid includes a custom query, selected fields from table including a
    virtual field, a column with data not found in a table, accesses data with
    a left join and formats data prior to display.

    The ComplexJqGrid class has a custom data method. By overriding the JqGrid
    data method, data can be arranged and formatted however you like, as long
    as the number of fields in the rows match the fields in the colModel.
    """
    response.generic_patterns = ['html']

    jqgrid = ComplexJqGrid(globals(), db.things,
            jqgrid_options={
                'colModel': [
                    {'name': 'name', 'index': 'name'},
                    {'name': 'category', 'index': 'category'},
                    {'name': 'cost', 'index': 'cost', 'align': 'right'},
                    {'name': 'price', 'index': 'price', 'align': 'right'},
                    {'name': 'markup', 'index': 'markup', 'align': 'right'},
                    {'name': 'reduced', 'index': 'reduced', 'align': 'center'},
                    ],
                'caption': 'Complex data representation',
                'height': 300,
                'sortname': 'cost',
                'sortorder': 'desc',
                },
            query=db.things.category == request.args(0)
            )
    return dict(jqgrid=jqgrid())


class WebServiceJqGrid(JqGrid):

    @classmethod
    def data(cls, environment, table, query=None, orderby=None, fields=None):
        """Method for accessing jqgrid row data.

        Args:
            See JqGrid data method.
        Returns
            See JqGrid data method.
        """
        import urllib2
        from xml.dom import minidom
        request = environment['request']
        rows = []
        page = int(request.vars.page)
        pagesize = int(request.vars.rows)
        url = 'http://api.geonames.org/countryInfo?username=demo'
        xmldoc = minidom.parse(urllib2.urlopen(url))
        countries = []
        for x in range(1, len(xmldoc.firstChild.childNodes)):
            if not xmldoc.firstChild.childNodes[x].nodeName == 'country':
                continue
            vals = []
            country = xmldoc.firstChild.childNodes[x]
            for i in [1, 3, 13, 15]:
                try:
                    value = country.childNodes[i].firstChild.data,
                except:
                    value = ''
                vals.append(value)
            countries.append(dict(cell=vals))
        try:
            rows = countries[page * pagesize - pagesize: page * pagesize]
        except:
            rows = []
        total_records = len(countries)
        total_pages = int(math.ceil(total_records / float(pagesize)))
        return dict(
                total=total_pages,
                page=min(page, total_pages),
                rows=rows,
                records=total_records)


def web_service():
    """Illustrates displaying jqgrid table with data accessed from a webservice.

    The WebServiceJqGrid class has a custom data method.
    """
    response.generic_patterns = ['html']

    jqgrid = WebServiceJqGrid(globals(), db.things,
            orderby='',             # Prevent setting default
            jqgrid_options={
                'colModel': [
                    {'name': 'code', 'index': 'code'},
                    {'name': 'name', 'index': 'name'},
                    {'name': 'continent', 'index': 'continent'},
                    {'name': 'capital', 'index': 'capital'},
                    ],
                'caption': 'Countries of the world from geonames webservice',
                'height': 400,
                'sortname': 'code',
                'sortorder': 'desc',
                },
            )
    return dict(jqgrid=jqgrid())


def callback_demo():
    """Illustrates setting the select_callback_url.

    When the select_callback_url is set, when a row in the jqgrid table is
    clicked, the page redirects to indicated url.

    JqGrid makes use of jqgrid's onSelectRow event handler.
    http://www.trirand.com/jqgridwiki/doku.php?id=wiki:events

    If present in the url, the placeholder '{id}' is replaced with the id of
    the record represented by the row.
    """
    response.generic_patterns = ['html']
    return dict(foo=JqGrid(
        globals(),
        db.things,
        jqgrid_options={'caption': "Click a row to trigger callback."},
        select_callback_url=URL(r=request, f='select_callback/{id}')
        )())


def select_callback():
    """Callback for callback_demo().

    request.args(0): the id of the db.things record.
    """
    response.generic_patterns = ['html']
    rows = db(db.things.id == request.args(0)).select()
    return {'': BEAUTIFY(rows[0])}


def toolbar_searching():
    """Illustrates jqgrid Toolbar Searching.

    http://www.trirand.com/jqgridwiki/doku.php?id=wiki:toolbar_searching
    """
    response.generic_patterns = ['html']
    return dict(foo=JqGrid(globals(), db.things,
        filter_toolbar_options={
            # this is the only option supported so far, default is True
            'searchOnEnter': False
            },
        jqgrid_options={
            'colModel': [       # Use 'search':False to disable some columns
              {'name': 'id', 'index':'id', 'width': 55},
              {'name': 'name', 'index':'name'},
              {'name': 'category', 'index':'category',
                'stype':'select',
                'editoptions':{
                    'multiple':True,
                    'value':":;" + ';'.join('%s:%s' % (r['id'], r['name'])
                        for r in db(db.category.id > 0).select(
                        db.category.id, db.category.name))
                    },
                },
              {'name': 'price', 'index':'price'},
              {'name': 'owner', 'index':'owner'}
            ],
            'caption': 'Enter values in first row to filter results.',
            },
        )())


def form_editing():
    """Illustrates jqgrid Form Editing.

    http://www.trirand.com/jqgridwiki/doku.php?id=wiki:form_editing
    """
    response.generic_patterns = ['html']
    JS_FUNCTION = local_import('jqgrid', reload=True).Raw
    return dict(foo=JqGrid(globals(), db.things,
        # as of 2011-08-03 navGrid Search not implemented
        nav_grid_options={'add': True, 'edit': True, 'del': True,
            'search': False},
        jqgrid_options={
            'colModel': [
              {
                  'name': 'id',
                  'index':'id',
                  #'editable': False,            # This is the default
                  'width': 55,
              },
              {
                  'name': 'name',
                  'index':'name',
                  'editable': True,
              },
              {
                  'name': 'category',
                  'index':'category',
                  'stype':'select',
                  'editable': True,
                  'edittype':'select',          # Turns input into drop down
                  'editoptions': {
                    'value': ":;" + ';'.join('%s:%s' % (r['id'], r['name'])
                        for r in db(db.category.id > 0).select(
                        db.category.id, db.category.name))
                  },
              },
              {
                  'name': 'price',
                  'index':'price',
                  'editable': True,
              },
              {
                  'name': 'owner',
                  'index':'owner',
                  'editable': True,
              },
              {
                  'name': 'expire',
                  'index': 'expire',
                  'width': 100,
                  'editable': True,
                  'editoptions': {
                      'dataInit': JS_FUNCTION("""
                          function(el) {
                            setTimeout( function() {
                                $(el).datepicker({dateFormat: 'yy-mm-dd'});
                            }, 200);
                          }"""),
                  },
              },
            ],
            'caption': 'Select row and click Add/Edit/Del icons in nav bar.',
            },
        )())


def form_editing_custom():
    """Illustrates customizing the jqgrid Form Editing form.

    nav_add_options and nav_edit_options conform to the editGridRow properies
    http://www.trirand.com/jqgridwiki/doku.php?id=wiki:form_editing
    """
    response.generic_patterns = ['html']
    JS_FUNCTION = local_import('jqgrid', reload=True).Raw
    return dict(foo=JqGrid(globals(), db.things,
        nav_grid_options={'add': True, 'edit': True, 'del': True,
            'search': False},
        nav_add_options={'closeAfterAdd': True, 'width': 500},
        nav_edit_options={'closeAfterEdit': True, 'width': 500},
        jqgrid_options={
            'colModel': [
              {
                  'name': 'id',
                  'index':'id',
                  'width': 55,
              },
              {
                  'name': 'name',
                  'index':'name',
                  'editable': True,
              },
              {
                  'name': 'category',
                  'index':'category',
                  'stype':'select',
                  'editable': True,
                  'edittype':'select',          # Turns input into drop down
                  'editoptions': {
                    'value': ":;" + ';'.join('%s:%s' % (r['id'], r['name'])
                        for r in db(db.category.id > 0).select(
                        db.category.id, db.category.name))
                  },
              },
              {
                  'name': 'price',
                  'index':'price',
                  'editable': True,
              },
              {
                  'name': 'owner',
                  'index':'owner',
                  'editable': True,
              },
              {
                  'name': 'expire',
                  'index': 'expire',
                  'width': 100,
                  'editable': True,
                  'editoptions': {
                      'dataInit': JS_FUNCTION("""
                          function(el) {
                            setTimeout( function() {
                                $(el).datepicker({dateFormat: 'yy-mm-dd'});
                            }, 200);
                          }"""),
                  },
              },
            ],
            'caption': 'Select row and click Add/Edit/Del icons in nav bar.',
            },
        )())
