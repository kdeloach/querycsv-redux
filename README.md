![Build Status](https://github.com/kdeloach/querycsv-redux/actions/workflows/python-package.yml/badge.svg)

# querycsv-redux

Execute SQL code against data contained in one or more comma-separated-value
(CSV) files.

## Usage
```
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
```

## Usage Notes
  *  The first line of the file should contain the names of the columns.

  *  Table names used in the SQL should match the input CSV file names,
     without either the leading path or the trailing filename extension.

  *  When multiple input files (or a sqlite file with multiple tables)
     are used, SQL JOIN clauses can be used to combine the data.

  *  When a SQL script file is used instead of a single SQL commmand on
     the command line, only the output of the last SQL command will be displayed.

  *  Output to the console (the default) is formatted for readability.
     Output to a disk file is formatted as CSV, with commas delimiting
     columns and double quotes around strings.

  *  The primary intended purpose of a command-line SQL statement is to
     execute a SELECT or UNION statement against the data, and UPDATE
     and INSERT statements do not have any effect on input CSV file(s).
     An effect equivalent to an UPDATE statement can be achieved with
     SELECT statements, however, with output directed to a new CSV file.
     To perform an INSERT opertation it is necessary to either save the
     data in a Sqlite file or to use a script file with separate INSERT
     and SELECT statements.

  *  The SQL language features that can be used with querycsv are those
     supported by the Sqlite language (http://www.sqlite.org/lang.html).

## Examples
```sh
$ querycsv.py -i FL_insurance_sample.csv "PRAGMA table_info([FL_insurance_sample])"
 cid | name               | type | notnull | dflt_value | pk
=============================================================
 0   | policyID           |      | 0       | None       | 0
 1   | statecode          |      | 0       | None       | 0
 2   | county             |      | 0       | None       | 0
 3   | eq_site_limit      |      | 0       | None       | 0
 4   | hu_site_limit      |      | 0       | None       | 0
 5   | fl_site_limit      |      | 0       | None       | 0
 6   | fr_site_limit      |      | 0       | None       | 0
 7   | tiv_2011           |      | 0       | None       | 0
 8   | tiv_2012           |      | 0       | None       | 0
 9   | eq_site_deductible |      | 0       | None       | 0
 10  | hu_site_deductible |      | 0       | None       | 0
 11  | fl_site_deductible |      | 0       | None       | 0
 12  | fr_site_deductible |      | 0       | None       | 0
 13  | point_latitude     |      | 0       | None       | 0
 14  | point_longitude    |      | 0       | None       | 0
 15  | line               |      | 0       | None       | 0
 16  | construction       |      | 0       | None       | 0
 17  | point_granularity  |      | 0       | None       | 0
 ```
 ```
$ querycsv.py -i FL_insurance_sample.csv "select county, count(*) from FL_insurance_sample group by county having count(*) > 1000 order by county"
 county              | count(*)
================================
 BROWARD COUNTY      | 3193
 DUVAL COUNTY        | 1894
 HILLSBOROUGH COUNTY | 1166
 MARION COUNTY       | 1138
 MIAMI DADE COUNTY   | 4315
 OKALOOSA COUNTY     | 1115
 ORANGE COUNTY       | 1811
 PALM BEACH COUNTY   | 2791
 PINELLAS COUNTY     | 1774
 POLK COUNTY         | 1629
 SEMINOLE COUNTY     | 1100
 VOLUSIA COUNTY      | 1367
 ```

## Release Checklist
1. Update `PKG-INFO` version
1. Update `querycsv/querycsv.py` version
1. Update `setup.py` version
1. Commit version (ex. `4.1.0`)
1. Tag HEAD (ex. `v4.1.0`)
1. Push HEAD and tags
