"""
0.py

Place any app wide initialization here. This code gets run before any other
models.
"""
import os
from gluon.custom_import import track_changes, is_tracking_changes

DEBUG = False
if os.environ.get('WEB2PY_SERVER_MODE', 'live') == 'test':
    DEBUG = True
    if not is_tracking_changes():
        track_changes()
