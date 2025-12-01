# This file contains the WSGI configuration required to serve up your
# web application at http://yourusername.pythonanywhere.com/
# It works by setting the variable 'application' to a WSGI handler of some
# description.

import sys
import os

# Add your project directory to the Python path
# Update this path to match your PythonAnywhere username and directory
# Based on error log, the path is:
path = '/home/NabuaWasteManagement/Nabua-Waste-Management'
if path not in sys.path:
    sys.path.insert(0, path)

# Change to the project directory
os.chdir(path)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'

# Import your Flask application
# This will trigger the initialization code
try:
    from app import app as application
    print("✅ Flask app imported successfully")
except Exception as e:
    print(f"❌ Error importing Flask app: {e}")
    import traceback
    traceback.print_exc()
    # Create a minimal error application
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def error():
        return f"Error loading application: {str(e)}", 500

if __name__ == "__main__":
    application.run()
