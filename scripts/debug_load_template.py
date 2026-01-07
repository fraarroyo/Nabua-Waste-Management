import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
import traceback

with app.app_context():
    try:
        tmpl = app.jinja_env.get_template('collection_team.html')
        print('Template loaded OK')
    except Exception:
        traceback.print_exc()