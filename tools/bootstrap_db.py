#!/usr/bin/env python3
"""Boot the r2 app briefly to trigger automatic DB/CF creation.

Usage: python tools/bootstrap_db.py [--ini PATH_TO_INI]

Defaults to `r2/example.ini` and will load the PasteDeploy app which
initializes pylons app globals and triggers model/table creation when
`db_create_tables` is enabled in the ini.
"""
import argparse
import importlib
import os
import queue
import sys
import time

from paste.deploy import loadapp

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ini', default='r2/example.ini', help='Path to ini (relative to repo root or absolute)')
    args = parser.parse_args()

    ini_path = args.ini

    # Resolve paths
    if not os.path.isabs(ini_path):
        ini_path = os.path.abspath(ini_path)

    if not os.path.exists(ini_path):
        print('INI file not found:', ini_path)
        return 2

    # The `relative_to` argument should be the directory containing the ini
    relative_to = os.path.dirname(ini_path)

    # Ensure the package import path includes the r2 package root
    repo_root = os.path.dirname(relative_to) if os.path.basename(relative_to) == 'r2' else relative_to
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    # Invalidate import caches so new path is recognized
    importlib.invalidate_caches()

    # Some tests expect this
    try:
        import baseplate.events
        baseplate.events.EventQueue = queue.Queue
    except Exception:
        pass

    print('Loading app from', ini_path)
    # Use PasteDeploy to load the app. This will initialize pylons app_globals
    # and (importantly) execute module-level code that creates tables/CFs
    # when `db_create_tables` is enabled in the ini.
    app_spec = 'config:' + os.path.basename(ini_path)
    try:
        wsgiapp = loadapp(app_spec, relative_to=relative_to)
    except Exception as e:
        print('Error loading app:', e)
        return 3

    # Allow a short pause for any background initialization
    print('App loaded; waiting briefly for DB initialization to complete...')
    time.sleep(3)
    print('Done. If Postgres/Cassandra were reachable and `db_create_tables` is true, tables/CFs should be created.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
