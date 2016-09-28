#!/usr/bin/env python
"""
Executes SQL on a delimited text file.

Copyright (c) 2008, R.Dreas Nielsen
Licensed under the GNU General Public License version 3.
Syntax:
    querycsv -i <csv file>... [-o <fname>] [-f <sqlite file>]
        (-s <fname>|<SELECT stmt>)
    querycsv -u <sqlite file> [-o <fname>] (-s <fname>|<SELECT stmt>)
    querycsv (-h|-V)
Options:
   -i <fname> Input CSV file name.
              Multiple -i options can be used to specify more than one input
              file.
   -u <fname> Use the specified sqlite file for input.
              Options -i and -f, are ignored if -u is specified
   -o <fname> Send output to the named CSV file.
   -s <fname> Execute a SQL script from the file given as the argument.
              Output will be displayed from the last SQL command in
              the script.
   -f <fname> Use a sqlite file instead of memory for intermediate storage.
   -h         Print this help and exit.
   -V         Print the version number.
Notes:
   1. Table names used in the SQL should match the input CSV file names,
      without the ".csv" extension.
   2. When multiple input files or an existing sqlite file are used,
      the SQL can contain JOIN expressions.
   3. When a SQL script file is used instead of a single SQL command on
      the command line, only the output of the last command will be
      displayed.
"""
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import sys
import os.path
import getopt
import csv
import sqlite3

from contextlib import contextmanager

VERSION = "4.1.0"


# Source: Aaron Watters posted to gadfly-rdbms@egroups.com 1999-01-18
# Modified version taken from sqliteplus.py by Florent Xicluna
def pretty_print(rows, fp):
    headers = rows.pop(0)
    rows = [[unicode(col) for col in row] for row in rows]

    rcols = range(len(headers))

    colwidth = [max(0, len(headers[i])) for i in xrange(len(headers))]
    for y in xrange(len(rows)):
        for x in xrange(len(headers)):
            colwidth[x] = max(colwidth[x], len(rows[y][x]))

    # Header
    fp.write(' ' + ' | '.join([unicode(headers[i]).ljust(colwidth[i])
                               for i in rcols]) + '\n')

    # Seperator
    num_dashes = sum(colwidth) + 3 * len(headers) - 1
    fp.write('=' * num_dashes + '\n')

    # Rows
    for row in rows:
        fp.write(' ' + ' | '.join([row[i].ljust(colwidth[i])
                                   for i in rcols]) + '\n')

    if len(rows) == 0:
        fp.write('No results\n')


def write_csv(rows, fp):
    csvout = csv.writer(fp, quoting=csv.QUOTE_NONNUMERIC)
    csvout.writerows(rows)


def read_sqlfile(filename):
    """
    Open the text file with the specified name, read it, and return a list of
    the SQL statements it contains.
    """
    # Currently (11/11/2007) this routine knows only two things about SQL:
    #    1. Lines that start with "--" are comments.
    #    2. Lines that end with ";" terminate a SQL statement.
    sqlfile = open(filename, "rt")
    sqlcmds = []
    currcmd = ''
    for line in sqlfile:
        line = line.strip()
        if len(line) > 0 and not (len(line) > 1 and line[:2] == "--"):
            currcmd = "%s %s" % (currcmd, line)
            if line[-1] == ';':
                sqlcmds.append(currcmd.strip())
                currcmd = ''
    return sqlcmds


def as_list(item):
    """Wrap `item` in a list if it isn't already one."""
    if isinstance(item, (str, unicode)):
        return [item]
    return item


@contextmanager
def as_connection(db):
    if isinstance(db, (str, unicode)):
        with sqlite3.connect(db) as conn:
            yield conn
    else:
        yield db

def import_array(db, array, table_name, overwrite=False):

    with as_connection(db) as conn:
        if table_exists(conn, table_name) and not overwrite:
            return

        column_names = array[0]
        colstr = ",".join('[{0}]'.format(col) for col in column_names)
        conn.execute('drop table if exists %s;' % table_name)
        conn.execute('create table %s (%s);' % (table_name, colstr))
        for row in array[1:]:
            vals = [cell for cell in row]
            params = ','.join('?' for i in range(len(vals)))
            sql = 'insert into %s values (%s);' % (table_name, params)
            conn.execute(sql, vals)
        conn.commit()

def import_csv(db, filename, table_name=None, overwrite=False):
    table_name = table_name if table_name else get_table_name(filename)

    with as_connection(db) as conn:
        if table_exists(conn, table_name) and not overwrite:
            return

        dialect = csv.Sniffer().sniff(open(filename, 'r').readline())
        reader = csv.reader(open(filename, 'r'), dialect)
        column_names = reader.next()
        colstr = ",".join('[{0}]'.format(col) for col in column_names)
        conn.execute('drop table if exists %s;' % table_name)
        conn.execute('create table %s (%s);' % (table_name, colstr))
        for row in reader:
            vals = [unicode(cell, 'utf-8') for cell in row]
            params = ','.join('?' for i in range(len(vals)))
            sql = 'insert into %s values (%s);' % (table_name, params)
            conn.execute(sql, vals)
        conn.commit()


def table_exists(conn, table_name):
    try:
        conn.execute('select 1 from {0}'.format(table_name))
        return True
    except sqlite3.OperationalError:
        return False


def execute_sql(conn, sqlcmds):
    """
    Parameters
    ----------
    conn: Database connection that conforms to the Python DB API.
    sqlcmds: List of SQL statements, to be executed in order.
    """
    curs = conn.cursor()
    for cmd in sqlcmds:
        curs.execute(cmd)
    headers = tuple([item[0] for item in curs.description])
    return [headers] + curs.fetchall()


def query_sqlite(sqlcmd, sqlfilename=None):
    """
    Run a SQL command on a sqlite database in the specified file
    (or in memory if sqlfilename is None).
    """
    database = sqlfilename if sqlfilename else ':memory:'
    with as_connection(database) as conn:
        return execute_sql(conn, as_list(sqlcmd))


def query_sqlite_file(scriptfile, *args, **kwargs):
    """
    Run a script of SQL commands on a sqlite database in the specified
    file (or in memory if sqlfilename is None).
    """
    cmds = read_sqlfile(scriptfile)
    return query_sqlite(cmds, *args, **kwargs)


def query_csv(sqlcmd, infilenames, file_db=None):
    """
    Query the listed CSV files, optionally writing the output to a
    sqlite file on disk.
    """
    database = file_db if file_db else ':memory:'
    with as_connection(database) as conn:
        for csvfile in as_list(infilenames):
            import_csv(conn, csvfile)
        return execute_sql(conn, as_list(sqlcmd))


def get_table_name(csvfile):
    head, tail = os.path.split(csvfile)
    return os.path.splitext(tail)[0]


def query_csv_file(scriptfile, *args, **kwargs):
    """
    Query the listed CSV files, optionally writing the output to a sqlite
    file on disk.
    """
    cmds = read_sqlfile(scriptfile)
    return query_csv(cmds, *args, **kwargs)


def print_help():
    print(__doc__.strip())


def main():
    optlist, arglist = getopt.getopt(sys.argv[1:], "i:u:o:f:Vhs")
    flags = dict(optlist)

    if '-V' in flags:
        print(VERSION)
        sys.exit(0)

    if len(arglist) == 0 or '-h' in flags:
        print_help()
        sys.exit(0)

    outfile = flags.get('-o', None)
    usefile = flags.get('-u', None)

    execscript = '-s' in flags
    sqlcmd = " ".join(arglist)

    if usefile:
        if execscript:
            # sqlcmd should be the script file name
            results = query_sqlite_file(sqlcmd, usefile)
        else:
            results = query_sqlite(sqlcmd, usefile)
    else:
        file_db = flags.get('-f', None)
        csvfiles = [opt[1] for opt in optlist if opt[0] == '-i']
        if len(csvfiles) > 0:
            if execscript:
                # sqlcmd should be the script file name
                results = query_csv_file(sqlcmd, csvfiles, file_db)
            else:
                results = query_csv(sqlcmd, csvfiles, file_db)
        else:
            print_help()
            sys.exit(1)

    if outfile:
        with open(outfile, 'wb') as fp:
            write_csv(results, fp)
    else:
        pretty_print(results, sys.stdout)


if __name__ == '__main__':
    main()
