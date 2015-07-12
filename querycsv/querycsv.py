#!/usr/bin/env python
"""
 querycsv.py

 Purpose:
   Execute SQL (conceptually, a SELECT statement) on an input file, and
   write the results to an output file.

 Author(s):
   R. Dreas Nielsen (RDN)

 Copyright and license:
   Copyright (c) 2008, R.Dreas Nielsen
   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   The GNU General Public License is available at
   <http://www.gnu.org/licenses/>

 Notes:
   1. The input files must be in a delimited format, such as a CSV file.
   2. The first line of each input file must contain column names.
   3. Default output is to the console in a readable format.  Output to
      a file is in CSV format.

 History:
   Date        Revisions
   -------     ---------------
   2/17/2008    First version.  One CSV file input, output only to CSV.  RDN.
   2/19/2008    Began adding code to allow multiple input files, or an
                existing sqlite file, to allow a sqlite file to be preserved,
                and to default to console output rather than CSV output.  RDN.
   2/20/2008    Completed coding of revisions.  RDN.
   2/22/2008    Added 'conn.close()' to 'qsqlite()'.  Corrected order of
                arguments to 'qsqlite()' in 'main()'. RDN.
   2/23/2008    Added 'commit()' after copying data into the sqlite file;
                otherwise it is not preserved.  Added the option to execute
                SQL commands from a script file. RDN.
"""
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import sys
import os.path
import getopt
import csv
import sqlite3

VERSION = "3.1.1"


def quote_str(s):
    if len(s) == 0:
        return "''"
    if len(s) == 1:
        if s == "'":
            return "''''"
        else:
            return "'%s'" % s
    if s[0] != "'" or s[-1:] != "'":
        return "'%s'" % s.replace("'", "''")
    return s


def quote_list(arr):
    return [quote_str(s) for s in arr]


def quote_list_as_str(arr):
    return ",".join(quote_list(arr))


# Source: Aaron Watters posted to gadfly-rdbms@egroups.com 1999-01-18
# Modified version taken from sqliteplus.py by Florent Xicluna
def pretty_print(rows, fp):
    headers = rows.pop(0)

    rcols = range(len(headers))
    rrows = range(len(rows))
    colwidth = [max(0, len(headers[j]),
                    *(len(str(rows[i][j])) for i in rrows)) for j in rcols]

    # Header
    fp.write(' ' + ' | '.join([headers[i].ljust(colwidth[i])
                               for i in rcols]) + '\n')

    # Seperator
    num_dashes = sum(colwidth) + 3 * len(headers) - 1
    fp.write('=' * num_dashes + '\n')

    # Rows
    for row in rows:
        fp.write(' ' + ' | '.join([str(row[i]).ljust(colwidth[i])
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
        vals = quote_list_as_str(row)
        sql = "insert into %s values (%s);" % (table_name, vals)
        db.execute(sql)
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
        return execute_sql(conn, [sqlcmd])


def query_sqlite_file(scriptfile, sqlfilename=None):
    """
    Run a script of SQL commands on a sqlite database in the specified
    file (or in memory if sqlfilename is None).
    """
    database = sqlfilename if sqlfilename else ':memory:'
    with sqlite3.connect(database) as conn:
        cmds = read_sqlfile(scriptfile)
        return execute_sql(conn, cmds)


def query_csv(sqlcmd, infilenames, file_db=None, keep_db=False):
    """
    Query the listed CSV files, optionally writing the output to a
    sqlite file on disk.
    """
    # Create a sqlite file, if specified
    if file_db:
        try:
            os.unlink(file_db)
        except:
            pass

    database = file_db if file_db else ':memory:'
    with sqlite3.connect(database) as conn:
        # Move data from input CSV files into sqlite
        for csvfile in infilenames:
            head, tail = os.path.split(csvfile)
            tablename = os.path.splitext(tail)[0]
            csv_to_sqldb(conn, csvfile, tablename)

            # Execute the SQL
            results = execute_sql(conn, [sqlcmd])

            if file_db and not keep_db:
                try:
                    os.unlink(file_db)
                except:
                    pass

            return results


def query_csv_file(scriptfile, infilenames, file_db=None, keep_db=False):
    """
    Query the listed CSV files, optionally writing the output to a sqlite
    file on disk.
    """
    # Create a sqlite file, if specified
    if file_db:
        try:
            os.unlink(file_db)
        except:
            pass

    database = file_db if file_db else ':memory:'
    with sqlite3.connect(database) as conn:
        # Move data from input CSV files into sqlite
        for csvfile in infilenames:
            head, tail = os.path.split(csvfile)
            tablename = os.path.splitext(tail)[0]
            csv_to_sqldb(conn, csvfile, tablename)

        # Execute the SQL
        cmds = read_sqlfile(scriptfile)
        results = execute_sql(conn, cmds)

        # Clean up.
        conn.close()
        if file_db and not keep_db:
            try:
                os.unlink(file_db)
            except:
                pass

        return results


def print_help():
    print("""querycsv {0} -- Executes SQL on a delimited text file.
Copyright (c) 2008, R.Dreas Nielsen
Licensed under the GNU General Public License version 3.
Syntax:
    querycsv -i <csv file>... [-o <fname>] [-f <sqlite file> [-k]]
        (-s <fname>|<SELECT stmt>)
    querycsv -u <sqlite file> [-o <fname>] (-s <fname>|<SELECT stmt>)
Options:
   -i <fname> Input CSV file name.
              Multiple -i options can be used to specify more than one input
              file.
   -u <fname> Use the specified sqlite file for input.
              Options -i, -f, and -k are ignored if -u is specified
   -o <fname> Send output to the named CSV file.
   -s <fname> Execute a SQL script from the file given as the argument.
              Output will be displayed from the last SQL command in
              the script.
   -f <fname> Use a sqlite file instead of memory for intermediate storage.
   -k         Keep the sqlite file when done (only valid with -f).
   -h         Print this help and exit.
Notes:
   1. Table names used in the SQL should match the input CSV file names,
      without the ".csv" extension.
   2. When multiple input files or an existing sqlite file are used,
      the SQL can contain JOIN expressions.
   3. When a SQL script file is used instead of a single SQL command on
      the command line, only the output of the last command will be
      displayed.""".format(VERSION))


def main():
    optlist, arglist = getopt.getopt(sys.argv[1:], "i:u:o:f:khs")
    flags = dict(optlist)

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
        keep_db = '-k' in flags
        csvfiles = [opt[1] for opt in optlist if opt[0] == '-i']
        if len(csvfiles) > 0:
            if execscript:
                # sqlcmd should be the script file name
                results = query_csv_file(sqlcmd, csvfiles, file_db, keep_db)
            else:
                results = query_csv(sqlcmd, csvfiles, file_db, keep_db)
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
