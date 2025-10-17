# This file contains the WSGI configuration required to serve up your
# web application at http://yourusername.pythonanywhere.com/
# It works by setting the variable 'application' to a WSGI handler of some
# description.

import sys
import os

# Add your project directory to the Python path
path = '/home/fraarroyo/Nabua-Waste-Management'
if path not in sys.path:
    sys.path.append(path)

# Import your Flask application
from app import app as application

# Optional: Set environment variables
os.environ['FLASK_ENV'] = 'production'

if __name__ == "__main__":
    application.run()
