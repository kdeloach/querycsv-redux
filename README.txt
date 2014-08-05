querycsv.py
Execute SQL code against data contained in one or more comma-separated-value 
(CSV) files.

querycsv.py is a Python module and program that allows you to use SQL
to extract and summarize data from one or more delimited (e.g., CSV) files.


Syntax and Options
==================

querycsv.py -i <fname> [other options] [SELECT_stmt]

Arguments
---------

   SELECT_stmt
      A SQL statement (which must be quoted) that is to be executed
	  against the CSV file(s) that are specified by the "-i" option.
	  This argument is optional and may be omitted if the "-f" option
	  is used to specify a SQL script file to use instead.
	  
Options
-------

   -i <fname> Input CSV file name.
              Multiple -i options can be used to specify more than one input file.
   -u <fname> Use the specified sqlite file for input.
              Options -i, -f, and -k are ignored if -u is specified
   -o <fname> Send output to the named CSV file.
   -s         Execute a SQL script from the file given as the argument.
   -f <fname> Use a sqlite file instead of memory for intermediate storage.
   -k         Keep the sqlite file when done (only valid with -f).
   -h         Print this help and exit.



Usage Notes
===========

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

