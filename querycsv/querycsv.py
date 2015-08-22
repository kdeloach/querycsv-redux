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

VERSION = "3.1.2"


# Source: Aaron Watters posted to gadfly-rdbms@egroups.com 1999-01-18
# Modified version taken from sqliteplus.py by Florent Xicluna
def pretty_print(rows, fp):
    headers = rows.pop(0)

    rcols = range(len(headers))
    rrows = range(len(rows))
    colwidth = [max(0, len(headers[j]),
                    *(len(rows[i][j]) for i in rrows)) for j in rcols]

    # Header
    fp.write(' ' + ' | '.join([headers[i].ljust(colwidth[i])
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


def commands(cmds):
    if isinstance(cmds, (str, unicode)):
        return [cmds]
    return cmds


def csv_to_sqldb(db, filename, table_name):
    dialect = csv.Sniffer().sniff(open(filename, "rt").readline())
    reader = csv.reader(open(filename, "rt"), dialect)
    column_names = reader.next()
    colstr = ",".join("[{0}]".format(col) for col in column_names)
    try:
        db.execute("drop table %s;" % table_name)
    except:
        pass
    db.execute("create table %s (%s);" % (table_name, colstr))
    for row in reader:
        vals = [unicode(cell, 'utf-8') for cell in row]
        params = ','.join('?' for i in range(len(vals)))
        sql = "insert into %s values (%s);" % (table_name, params)
        db.execute(sql, vals)
    db.commit()


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
    with sqlite3.connect(database) as conn:
        return execute_sql(conn, commands(sqlcmd))


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
    with sqlite3.connect(database) as conn:
        # Move data from input CSV files into sqlite
        for csvfile in infilenames:
            head, tail = os.path.split(csvfile)
            tablename = os.path.splitext(tail)[0]
            csv_to_sqldb(conn, csvfile, tablename)

            # Execute the SQL
            results = execute_sql(conn, commands(sqlcmd))

    return results


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
