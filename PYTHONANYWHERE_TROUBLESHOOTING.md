# PythonAnywhere Troubleshooting Guide

## Internal Server Error - Common Fixes

### 1. Check Error Logs
On PythonAnywhere, go to:
- **Web tab** → **Error log** (scroll down)
- Look for the actual error message

### 2. Common Issues and Solutions

#### Issue: Database Path Error
**Error:** `OperationalError: unable to open database file`

**Solution:**
```bash
# In PythonAnywhere Bash console
cd /home/fraarroyo/Nabua-Waste-Management
mkdir -p instance
chmod 755 instance
```

#### Issue: Missing Dependencies
**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
# Make sure you're in the virtual environment
workon nabua-waste

# Install dependencies
pip install -r requirements_pythonanywhere_py313.txt
```

#### Issue: Database Not Initialized
**Error:** `Table doesn't exist`

**Solution:**
```bash
# In PythonAnywhere Bash console
cd /home/fraarroyo/Nabua-Waste-Management
python3.10 -c "from app import app, db; app.app_context().push(); db.create_all()"
python3.10 -c "from add_nabua_barangays import add_nabua_barangays; add_nabua_barangays()"
```

#### Issue: Import Error
**Error:** `ImportError: cannot import name 'app'`

**Solution:**
1. Check WSGI file path in Web tab
2. Make sure the path in `pythonanywhere_wsgi.py` matches your actual directory:
   ```python
   path = '/home/YOUR_USERNAME/Nabua-Waste-Management'
   ```

### 3. Manual Database Initialization

If automatic initialization fails, run this in Bash console:

```bash
cd /home/fraarroyo/Nabua-Waste-Management
python3.10
```

Then in Python:
```python
from app import app, db, User, Barangay
app.app_context().push()
db.create_all()

# Load barangays
from add_nabua_barangays import add_nabua_barangays
add_nabua_barangays()

# Create admin user if needed
admin = User.query.filter_by(username='admin').first()
if not admin:
    from werkzeug.security import generate_password_hash
    admin = User(
        username='admin',
        email='admin@nabua.gov.ph',
        full_name='System Administrator',
        role='admin'
    )
    admin.password_hash = generate_password_hash('admin123')
    db.session.add(admin)
    db.session.commit()
    print("Admin user created!")
else:
    print("Admin user already exists")
```

### 4. Check File Permissions

```bash
# Make sure files are readable
chmod 644 app.py
chmod 644 pythonanywhere_wsgi.py
chmod -R 755 templates/
chmod -R 755 instance/
```

### 5. Verify WSGI Configuration

In PythonAnywhere Web tab:
- **Source code:** `/home/fraarroyo/Nabua-Waste-Management`
- **Working directory:** `/home/fraarroyo/Nabua-Waste-Management`
- **WSGI configuration file:** `/var/www/fraarroyo_pythonanywhere_com_wsgi.py`

Edit the WSGI file and make sure it points to:
```python
path = '/home/fraarroyo/Nabua-Waste-Management'
```

### 6. Test Import Manually

In Bash console:
```bash
cd /home/fraarroyo/Nabua-Waste-Management
python3.10 -c "from app import app; print('Import successful!')"
```

If this fails, check the error message.

### 7. Check Python Version

Make sure you're using Python 3.10 or 3.13:
```bash
python3.10 --version
# or
python3.13 --version
```

### 8. Reload Web App

After making changes:
1. Go to **Web tab**
2. Click **Reload** button
3. Wait a few seconds
4. Try accessing your site again

### 9. Common Error Messages

| Error | Solution |
|-------|----------|
| `500 Internal Server Error` | Check error log in Web tab |
| `ModuleNotFoundError` | Install missing dependencies |
| `Table doesn't exist` | Run `db.create_all()` |
| `Permission denied` | Check file permissions |
| `No such file or directory` | Verify file paths |

### 10. Get Help

If you're still stuck:
1. Copy the full error message from the error log
2. Check which line in the code is causing the error
3. Verify all files are uploaded correctly
4. Make sure virtual environment is activated

