#!/usr/bin/env python

"""Greasemonkey statistics gathering client.

This tool parses the JSON data stored in the SQLite database."""

import collections
import json
import sqlite3
import sys

import numpy


def _Submissions():
  """All submitted data."""
  con = sqlite3.connect('stats.db')
  cur = con.cursor()
  cur.execute('SELECT data FROM stats')
  while True:
    row = cur.fetchone()
    if row is None: break
    yield json.loads(row[0])


def _LatestSubmissions():
  """The most recent submission from each user_id."""
  con = sqlite3.connect('stats.db')
  cur = con.cursor()
  cur.execute(
      'SELECT data FROM stats '
      'JOIN ( '
      '    SELECT user_id, MAX(time) AS time '
      '    FROM stats GROUP BY user_id ) AS last '
      'ON stats.user_id = last.user_id AND stats.time = last.time')
  while True:
    row = cur.fetchone()
    if row is None: break
    yield json.loads(row[0])


def Grants():
  cnt_explicit = 0
  cnt_explicit_none = 0
  cnt_implicit = 0
  cnt_none = 0
  cnt_scripts = 0

  for data in _LatestSubmissions():
    for script in data['scripts']:
      cnt_scripts += 1
      if script['implicitGrants'] and not (
          len(script['implicitGrants']) == 1
          and script['implicitGrants'][0].strip() == 'none'
          ):
        cnt_implicit += 1
      elif script['explicitGrants']:
        if (
            len(script['explicitGrants']) == 1
            and script['explicitGrants'][0].strip() == 'none'
            ):
          cnt_explicit_none += 1
        else:
          cnt_explicit += 1
      else:
        cnt_none += 1

  print 'Num scripts:', cnt_scripts
  print 'Num with explicit none:', cnt_explicit_none
  print 'Num with explicit grants:', cnt_explicit
  print 'Num with implicit grants:', cnt_implicit
  print 'Num with no grants:', cnt_none


def Imperatives():
  imperatives = collections.defaultdict(int)
  scripts = 0

  for data in _LatestSubmissions():
    for script in data['scripts']:
      scripts += 1
      for imperative in set(script['imperatives']):
        imperatives[imperative] += 1

  print 'Num scripts:', scripts
  for name, count in imperatives.iteritems():
    print '%10d\t%s' % (count, name)


def NumScriptsData():
  num = [len(x['scripts']) for x in _LatestSubmissions()]
  print '\n'.join([str(n) for n in num])


def NumScriptsStats():
  num = [len(x['scripts']) for x in _LatestSubmissions()]
  print 'Min   ', min(num)
  print 'Max   ', max(num)
  print 'Mean  ', numpy.mean(num)
  print 'Median', numpy.median(num)


def ScriptDomains():
  domains = collections.defaultdict(int)
  schemes = collections.defaultdict(int)
  for data in _LatestSubmissions():
    for script in data['scripts']:
      domains[script['installDomain']] += 1
      schemes[script['installScheme']] += 1

  print 'Domains:'
  for cnt, dom in sorted([(c, d) for (d, c) in domains.items()]):
    print '% 8d %s' % (cnt, dom)
  print 'Schemes:'
  for cnt, sch in sorted([(s, d) for (d, s) in schemes.items()]):
    print '% 8d %s' % (cnt, sch)


def main():
  if len(sys.argv) != 2:
    print 'Must supply job name argument.'
    sys.exit(1)

  job = globals().get(sys.argv[1], None)
  if job is not None:
    job()
  else:
    print 'Unknown job:', sys.argv[1]


if __name__ == '__main__':
  main()

