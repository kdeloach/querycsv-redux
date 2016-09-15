#!/usr/bin/env python
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import csv
import os.path
import unittest

from io import StringIO

from .querycsv import (query_csv, query_csv_file,
                       query_sqlite, import_csv,
                       pretty_print, as_connection,
                       import_array)

TEST_DIR = 'test_files'


def testfile(filename):
    return os.path.join(TEST_DIR, filename)


def create_csv(filename, content):
    create_test_folder()
    with open(filename, 'wb') as f:
        writer = csv.writer(f)
        rows = to_csv_rows(content)
        writer.writerows(rows)


def create_file(filename, content):
    create_test_folder()
    with open(filename, 'wb') as f:
        f.write(content)


def create_test_folder():
    try:
        os.makedirs(TEST_DIR)
    except OSError:
        pass


def to_csv_rows(content):
    return [[col.strip() for col in row.split(',')]
            for row in content.strip().split('\n')]


class TestQueryFunctions(unittest.TestCase):

    def setUp(self):
        self.db = testfile('db.sqlite3')
        self.foo = testfile('foo.csv')
        self.bar = testfile('bar.csv')
        create_csv(self.foo, """
            a, b, c
            1, 2, 3
            """)
        create_csv(self.bar, """
            a, b, c
            4, 5, 6
            """)
        self.array = [
            [u'name', u'number'],
            [u'cat', u'1'],
            [u'dog', u'2'],
            [u'bird', u'3']
            ]

    def tearDown(self):
        if os.path.exists(self.db):
            os.unlink(self.db)

    def assertMatch(self, results, content):
        rows = to_csv_rows(content)
        self.assertEqual(len(results), len(rows))
        for y in xrange(0, len(rows)):
            rowA = rows[y]
            rowB = results[y]
            self.assertEqual(len(rowA), len(rowB))
            for x in xrange(0, len(rowA)):
                a = str(rowA[x])
                b = str(rowB[x])
                self.assertEqual(a, b)

    def test_query_csv1(self):
        """Test query_csv with single table."""
        results = query_csv('select * from foo', self.foo)
        self.assertMatch(results, """
            a, b, c
            1, 2, 3
            """)

    def test_query_csv2(self):
        """Test query_csv with multiple tables."""
        results = query_csv('select * from foo union all '
                            'select * from bar',
                            [self.foo, self.bar])
        self.assertMatch(results, """
            a, b, c
            1, 2, 3
            4, 5, 6
            """)

    def test_query_csv3(self):
        """Test query_csv with multiple commands."""
        results = query_csv(['update foo set a=(a+b+c)',
                             'select a from foo'],
                            self.foo)
        self.assertMatch(results, """
            a
            6
            """)

    def test_query_csv_file(self):
        """Test query_csv_file."""
        query1 = testfile('query1.sql')
        create_file(query1, 'update foo set a=(a+b+c);\n'
                            'select a from foo;')
        results = query_csv_file(query1, self.foo)
        self.assertMatch(results, """
            a
            6
            """)

    def test_query_sqlite(self):
        """Test query_sqlite."""
        import_csv(self.db, self.foo, table_name='foo2')
        results = query_sqlite('select * from foo2', self.db)
        self.assertMatch(results, """
            a, b, c
            1, 2, 3
            """)

    def test_query_sqlite_overwrite1(self):
        """Test that tables are NOT overwritten when overwrite=False."""
        import_csv(self.db, self.foo, table_name='tmp')
        results = query_sqlite('select * from tmp', self.db)
        self.assertMatch(results, """
            a, b, c
            1, 2, 3
            """)

        import_csv(self.db, self.bar, table_name='tmp', overwrite=False)
        results = query_sqlite('select * from tmp', self.db)
        self.assertMatch(results, """
            a, b, c
            1, 2, 3
            """)

    def test_query_sqlite_overwrite2(self):
        """Test that tables ARE overwritten when overwrite=True."""
        import_csv(self.db, self.foo, table_name='tmp')
        results = query_sqlite('select * from tmp', self.db)
        self.assertMatch(results, """
            a, b, c
            1, 2, 3
            """)

        import_csv(self.db, self.bar, table_name='tmp', overwrite=True)
        results = query_sqlite('select * from tmp', self.db)
        self.assertMatch(results, """
            a, b, c
            4, 5, 6
            """)

    def test_pretty_print1(self):
        fp = StringIO()
        results = query_csv('select * from foo', self.foo)
        pretty_print(results, fp)
        self.assertEqual(fp.getvalue(),
                         ' a | b | c\n===========\n 1 | 2 | 3\n')

    def test_pretty_print2(self):
        fp = StringIO()
        results = query_csv('select count(*) from foo', self.foo)
        pretty_print(results, fp)
        self.assertEqual(fp.getvalue(),
                         ' count(*)\n==========\n 1       \n')

    def test_query_array1(self):
        import_array(self.db, self.array, 'result')
        results = query_sqlite('select * from result where name="dog"', self.db)
        self.assertEqual(results, [('name', 'number'), (u'dog', u'2')])

    def test_query_array2(self):
        with as_connection(':memory:') as db:
            import_array(db, self.array, 'result')
            results = query_sqlite('select * from result where name="dog"', db)
            self.assertEqual(results, [('name', 'number'), (u'dog', u'2')])

if __name__ == '__main__':
    unittest.main()
