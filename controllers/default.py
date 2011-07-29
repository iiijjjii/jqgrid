# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################
import logging

response.menu = [
    ('Customize', False, URL('customize'), []),
    ('One liner', False, URL('one_liner'), []),
    ('Subclass', False, URL('how_to_subclass'), []),
    ('Using View', False, URL('using_a_view'), []),
    ('Using View2', False, URL('using_a_view_2'), []),
    ('Components', False, URL('a_container_page_using_component'), []),
    ('Helper', False, URL('html_helper'), []),
    ('Query&Orderby', False, URL('query_and_order_by'), []),
    ('Callback', False, URL('callback_demo'), []),
    ('Searching', False, URL('toolbar_searching'), []),
    ]

JqGrid = local_import('jqgrid', app='jqgrid', reload=True).JqGrid
JqGrid.initialize_response_files(globals(), # Better have this explicitly
        theme='ui-lightness', # web2py's default base.css conflicts with smoothness
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
    return {'': 'Check out those demos and their source code, to know how to use'}


def obsolete(): # The original sample, showing how options can be customized
    jqgrid_options = { # all the basic jqgrid options go from here, in python
        'url': URL(f='call', args=['json', 'get_rows']), # must
        'colNames': ['ID', 'Name', 'Category', 'Price', 'Owner'], # optional
        'colModel': [ # optional
          {'name': 'id', 'index': 'id', 'width': 55},
          {'name': 'name', 'index': 'name'},
          {'name': 'category', 'index': 'category'},
          {'name': 'price', 'index': 'price'},
          {'name': 'owner', 'index': 'owner'}
        ],
        'caption': "You don't need a subclass to customize those simple options", # optional
        'rowNum': 40, # optional
        'rowList': [20, 40, 60], # optional
        }
    return dict(whatever_name_provided_that_we_dont_use_a_view=JqGrid(
            globals(),
            db.things,
            jqgrid_options = jqgrid_options,
            list_table_id = 'anything_you_like', # optional
            pager_div_id = 'and_this_too', # optional
        )
        () # So we don't even need a view!
        )

@service.json
def get_rows(): # also obsolete
    # Here is the chance to customize your own search criteria
    return JqGrid.data(
        globals(),
        db.things, # Don't you still need to tell JqGrid which table to deal with?
        fields=['id', 'name', 'category', 'price', 'owner']
        )

def customize():
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
    return dict(jqgrid=JqGrid(globals(), db.things,
        jqgrid_options=jqgrid_options)())


def one_liner(): # so you are a one-liner lover? :-)
    return dict(whatever=JqGrid(globals(), db.things)())

def how_to_subclass():
    class TalkativeJqgrid(JqGrid):
        # Usually only template is worthy to override
        template = '''
            jQuery(document).ready(function(){
              alert("Ready to init a jqGrid!"); // Just a demo
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
                {search: true, add: true, edit: true, del: true // I've changed here too
                });
              alert("jqGrid is loading/loaded!"); // Just a demo
            });''' # Warn: Make sure you keep those %(...)s intact
        # def data(self): return ...something new... # You might need this too
    jqgrid_options = {'caption': "A talkative JqGrid subclass"} # optional
    return dict(whatever=TalkativeJqgrid(
            globals(), db.category, jqgrid_options=jqgrid_options)())

def using_a_view(): # there is a view file for this
    return dict(jqgrid_stuff_but_not_callable=JqGrid(globals(), db.category)())
    # Notice the "()". So, what we transmit into the view, is something similar to a raw string.

def using_a_view_2(): # there is a view file for this
    return dict(jqgrid_callable_instance=JqGrid(globals(), db.category))
    # Get rid of the "()", if you prefer.

def a_container_page_using_component():
    # Here we assume you've invoked JqGrid.initialize_response_files(globals())
    return dict(blah = DIV( # Oh yes, you can move all following stuff into the view file.
        H1('So you love component?'),
        LOAD(request.controller, 'one_liner.load'),
        HR(),
        H1('Even better, many JqGrid components can appear at same page!'),
        LOAD(request.controller, 'using_a_view.load',
            # Note that if more than one JqGrid instance appears in same page,
            # each of them should have unique list_table_id and pager_div_id.
            # Lucky that JqGrid will try to define a unique id for you by default.
            # So in most cases you don't need to worry about that.
            ),
        ))

def html_helper():
    JQGRID = local_import('jqgrid').JQGRID
    return dict(blah = DIV(
        H1('This demo shows how JQGRID works like a native web2py html helper.'),
        HR(),
        JQGRID(globals(), db.things),
        ))

def wont_work():
    db.things.name.represent = lambda v: A(v, _href='index')
    # Cause a "JSON serialization error", therefore an empty output.
    return dict(whatever=JqGrid(globals(), db.things)())

def query_and_order_by():
    orderby = None
    if request.vars.sidx == 'price':
        orderby = db.things.price|db.things.name # customize a compound order
        if request.vars.sord == 'desc':
            orderby = ~db.things.price|~db.things.name
    # Mmm, sorting doesn't work quite well with reference field yet.
    # i.e. "category" in this demo db table
    # if request.vars.sidx == 'category':
    #     orderby = 'things.name'
    #     #if request.vars.sord == 'desc':
    #     #    orderby = ~orderby
    return dict(foo = JqGrid(
        globals(),
        db.things,
        query = db.things.price>500, # just for example
        orderby = orderby,
        jqgrid_options = {'caption': "Customizing query and order_by"},
        )())

def callback_demo():
    return dict(foo = JqGrid(
        globals(),
        db.things,
        select_callback_url = URL(r=request, f='select_callback/{id}')
        #select_callback_url = 'javascript:alert("You clicked #{id}")',
        )())

def select_callback():
    return {'': 'You clicked #%s'%request.args}

def toolbar_searching():
    return dict(foo=JqGrid(globals(), db.things,
            filter_toolbar_options = {
                'searchOnEnter': # only support this option so far
                    False # default is True
                },
            jqgrid_options = {
                'colModel': [ # Use 'search':False to disable some columns
                  {'name': 'id', 'index':'id', 'width': 55},
                  {'name': 'name', 'index':'name'},
                  {'name': 'category', 'index':'category',
                    'stype':'select',
                    'editoptions':{
                        'multiple':True,
                        'value':":;"+';'.join('%s:%s'%(r['id'], r['name'])
                            for r in db(db.category.id>0).select(
                            db.category.id, db.category.name))
                        },
                    },
                  {'name': 'price', 'index':'price'},
                  {'name': 'owner', 'index':'owner'}
                ],
                },
            )())
