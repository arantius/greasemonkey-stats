#!/usr/bin/env python

"""Greasemonkey statistics gathering server.

This is a FastCGI application which accepts incoming data over HTTP."""

import datetime
import json
import re
import socket
import sqlite3
import sys
from wsgiref import simple_server

from flup.server import fcgi


# The amount of time, in milliseconds, to ask clients to delay until their
# next report.
INTERVAL = 1000 * 60 * 60 * 24 * 7


def HandleData(environ, start_response):
  """Handle incoming data by persisting it."""
  do_redir = False
  if environ['REQUEST_METHOD'] == 'GET':
    # We accept data by PUT.  If we see a GET, redirect to documentation.
    start_response(
        '302 Redirect',
        [('Location',
          'http://www.greasespot.net/2012/11/anonymous-statistic-gathering.html'
         )]
        )
    return

  user_id = None
  time = datetime.datetime.utcnow().isoformat()
  m = re.search(r'^/submit/(\w+)$', environ['PATH_INFO'])
  if m:
    user_id = m.group(1)
  else:
    start_response('400 Bad request', [])
    yield 'Path not understood.'
    return
  data = environ['wsgi.input'].read(int(environ['CONTENT_LENGTH'], 10))

  conn = sqlite3.connect('stats.db')
  conn.execute(
      'INSERT INTO stats (user_id, time, data) VALUES (?, ?, ?)',
      (user_id, time, data)
      )
  conn.commit()

  start_response(
      '200 OK',
      [('Content-Type', 'application/json; charset=utf-8')]
      )
  resp = {
      'interval': INTERVAL,
      }
  yield json.dumps(resp, encoding='utf-8')


if __name__ == '__main__':
  if 'http' in sys.argv[0]:
    port = int(sys.argv[1], 10)
    httpd = simple_server.make_server('', port, HandleData)
    try:
      httpd.serve_forever()
    except KeyboardInterrupt:
      print
  elif 'fcgi' in sys.argv[0]:
    fcgi.WSGIServer(HandleData).run()

