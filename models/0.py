"""
0.py

Place any app wide initialization here. This code gets run before any other
models.
"""
# C0103: *Invalid name "%%s" (should match %%s)*
# pylint: disable=C0103

from gluon.custom_import import track_changes, is_tracking_changes
from applications.shared.modules.environ import server_production_mode

DEBUG = False
SERVER_MODE = server_production_mode(request)
if SERVER_MODE == 'test':
    DEBUG = True
    if not is_tracking_changes():
        track_changes()
