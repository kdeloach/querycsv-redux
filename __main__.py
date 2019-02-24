import os
import sys

# If we are running from a wheel, add the wheel to sys.path
if __package__ == '':
    # first dirname call strips of '/__main__.py', second strips off '/package'
    # Resulting path is the name of the wheel itself
    # Add that to sys.path so we can import package
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)

from querycsv.querycsv import main

if __name__ == '__main__':
    sys.exit(main())
