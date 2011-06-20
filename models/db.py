# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
#########################################################################

if request.env.web2py_runtime_gae:            # if running on Google App Engine
    db = DAL('google:datastore')              # connect to Google BigTable
                                              # optional DAL('gae://namespace')
    session.connect(request, response, db = db) # and store sessions and tickets there
    ### or use the following lines to store sessions in Memcache
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db = MEMDB(Client()))
else:                                         # else use a normal relational database
    db = DAL('sqlite://storage.sqlite')       # if not, use SQLite or other DB
## if no need for session
# session.forget()

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import *
mail = Mail()                                  # mailer
auth = Auth(globals(),db)                      # authentication/authorization
crud = Crud(globals(),db)                      # for CRUD helpers using auth
service = Service(globals())                   # for json, xml, jsonrpc, xmlrpc, amfrpc
plugins = PluginManager()

mail.settings.server = 'logging' or 'smtp.gmail.com:587'  # your SMTP server
mail.settings.sender = 'you@gmail.com'         # your email
mail.settings.login = 'username:password'      # your credentials or None

auth.settings.hmac_key = '<your secret key>'   # before define_tables()
auth.define_tables()                           # creates all needed tables
auth.settings.mailer = mail                    # for user email verification
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.messages.verify_email = 'Click on the link http://'+request.env.http_host+URL('default','user',args=['verify_email'])+'/%(key)s to verify your email'
auth.settings.reset_password_requires_verification = True
auth.messages.reset_password = 'Click on the link http://'+request.env.http_host+URL('default','user',args=['reset_password'])+'/%(key)s to reset your password'

#########################################################################
## If you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, uncomment and customize following
# from gluon.contrib.login_methods.rpx_account import RPXAccount
# auth.settings.actions_disabled=['register','change_password','request_reset_password']
# auth.settings.login_form = RPXAccount(request, api_key='...',domain='...',
#    url = "http://localhost:8000/%s/default/user/login" % request.application)
## other login methods are in gluon/contrib/login_methods
#########################################################################

crud.settings.auth = None                      # =auth to enforce authorization on crud

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

from gluon.contrib.populate import populate

db.define_table('category',
                Field('name', label='Name of Category'), format='%(name)s')

db.define_table('things',
                Field('name'),
                Field('quantity', 'integer'),
                Field('owner'),
                Field('price','double'),
                Field('category', db.category))

#db.things.category.represent = v.name


if db(db.things.id > 0).count() == 0:
    populate(db.category, 40)
    populate(db.things, 1000)


from gluon.contrib.simplejson import dumps
class JqGrid_obsolete(object):
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
        'caption': 'Test Grid',
        'height': '400px'
        }
    template = '''
        jQuery(document).ready(function(){
          jQuery("#%(list_table_id)s").jqGrid({
            complete: function(jsondata, stat) {
                if (stat == "success") {
                    var thegrid = jQuery("#%(list_table_id)s")[0];
                    thegrid.addJSONData(JSON.parse(jsondata.responseText).d);
                }
            },
            %(basic_options)s
          });
          jQuery("#%(list_table_id)s").jqGrid('navGrid', '#%(pager_div_id)s',
            {search: true, add: true, edit: false, del: false});
        });''' # Can be changed in subclass
    response_files = [ # experimental
        URL(r=request, c='static/jqueryui/css/smoothness', f='jquery-ui-1.8.12.custom.css'),
        URL(r=request, c='static/jquery.jqGrid/css', f='ui.jqgrid.css'),
        URL(r=request, c='static/jqueryui/js', f='jquery-ui-1.8.12.custom.min.js'),
        URL(r=request, c='static/jquery.jqGrid/src/i18n', f='grid.locale-en.js'),
        URL(r=request, c='static/jquery.jqGrid/js', f='jquery.jqGrid.min.js'), ]

    def __init__(self, table, jqgrid_options={}, pager_div_id='jqgrid_pager', list_table_id='jqgrid_list'):
        assert jqgrid_options['url'], 'You need to define it'
        self.table = table
        options = dict(self.default_options)
        options.update(jqgrid_options)
        options.setdefault('colNames', [f.label for f in table])
        options.setdefault('colModel', [{'name':f} for f in table.fields])
        options['pager'] = self.pager_div_id = pager_div_id
        self.list_table_id = list_table_id
        self.basic_options = dumps(options)[
            1:-1] # get rid of the quotation marks
        response.files.extend(self.response_files)

    def pager(self):
        return DIV(_id=self.pager_div_id)

    def list(self):
        return TABLE(_id=self.list_table_id)

    def script(self):
        return SCRIPT(self.template%self.__dict__)

    def __call__(self):
        return DIV(self.script(), self.list(), self.pager())

    @classmethod
    def data(self, table, fields=[]):
        # Implementation is mainly copied from original prototype
        rows = []
        page = int(request.vars.page)
        pagesize = int(request.vars.rows)
        limitby = (page * pagesize - pagesize, page * pagesize)
        orderby = table[request.vars.sidx]
        if request.vars.sord == 'desc':
            orderby = ~orderby
        for r in table._db(table.id > 0).select(limitby=limitby, orderby=orderby):
            vals = []
            for f in fields or table.fields:
                rep = table[f].represent
                if rep:
                    vals.append(rep(r[f]))
                else:
                    vals.append(r[f])
            rows.append(dict(id=r.id, cell=vals))
        total = table._db(table.id > 0).count()
        pages = int(total / pagesize)
        #if total % pagesize == 0: pages -= 1

        return dict(total=pages, page=page, rows=rows)
