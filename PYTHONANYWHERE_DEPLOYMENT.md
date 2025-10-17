# PythonAnywhere Deployment Guide

## 🚀 Deploying Nabua Waste Management System to PythonAnywhere

### Prerequisites
- PythonAnywhere account (free or paid)
- Git access to your repository

### Step 1: Upload Files to PythonAnywhere

1. **Clone your repository:**
   ```bash
   git clone https://github.com/fraarroyo/Nabua-Waste-Management.git
   cd Nabua-Waste-Management
   ```

2. **Or upload files manually:**
   - Upload all files from your project directory
   - Make sure to include the `templates/` folder
   - Upload the `instance/` folder if it exists

### Step 2: Set Up Python Environment

1. **Open a Bash console in PythonAnywhere**

2. **Create a virtual environment:**
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 nabua-waste
   workon nabua-waste
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements_pythonanywhere.txt
   ```

### Step 3: Initialize Database and Data

1. **Run the startup script:**
   ```bash
   python start_app.py
   ```

2. **Or manually initialize:**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   python -c "from add_nabua_barangays import add_nabua_barangays; add_nabua_barangays()"
   ```

### Step 4: Configure Web App

1. **Go to the Web tab in PythonAnywhere dashboard**

2. **Create a new web app:**
   - Choose "Manual Configuration"
   - Select Python 3.10
   - Choose your virtual environment: `nabua-waste`

3. **Set WSGI file:**
   - Edit the WSGI file
   - Replace the content with the content from `pythonanywhere_wsgi.py`

4. **Set working directory:**
   - Set to: `/home/fraarroyo/Nabua-Waste-Management`

### Step 5: Configure Static Files

1. **In the Web tab, add static file mappings:**
   - URL: `/static/`
   - Directory: `/home/fraarroyo/Nabua-Waste-Management/static/`

2. **If you don't have a static folder, create one:**
   ```bash
   mkdir static
   ```

### Step 6: Test Your Deployment

1. **Reload your web app** (click the reload button)

2. **Visit your site:**
   - `https://fraarroyo.pythonanywhere.com/`

3. **Test the login:**
   - Username: `admin`
   - Password: `admin123`

### Step 7: Verify Functionality

1. **Check if barangays are loaded:**
   - Go to "Add Waste" page
   - Verify you can see the barangay dropdown with 29 options

2. **Test waste item creation:**
   - Create a test waste item
   - Verify it appears in the dashboard

### Troubleshooting

#### If barangays don't appear:
1. **Check the console for errors:**
   ```bash
   python -c "from app import app, Barangay; app.app_context().push(); print('Barangays:', Barangay.query.count())"
   ```

2. **Force reload barangays:**
   ```bash
   python -c "from add_nabua_barangays import add_nabua_barangays; add_nabua_barangays()"
   ```

#### If database errors occur:
1. **Recreate database:**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.drop_all(); db.create_all()"
   ```

2. **Reinitialize data:**
   ```bash
   python start_app.py
   ```

#### If static files don't load:
1. **Check static file mapping in Web tab**
2. **Ensure static folder exists and has proper permissions**

### File Structure on PythonAnywhere

```
/home/fraarroyo/Nabua-Waste-Management/
├── app.py
├── add_nabua_barangays.py
├── pythonanywhere_wsgi.py
├── start_app.py
├── requirements_pythonanywhere.txt
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── add_waste.html
│   └── ...
├── instance/
│   └── waste_management.db
└── static/
    └── (create if needed)
```

### Environment Variables (Optional)

You can set these in the Web tab under "Environment variables":
- `FLASK_ENV=production`
- `SECRET_KEY=your-secret-key-here`

### Security Notes

1. **Change the admin password** after first login
2. **Set a strong SECRET_KEY** in production
3. **Consider using a paid plan** for better performance and reliability

### Support

If you encounter issues:
1. Check the PythonAnywhere error logs
2. Check the console for Python errors
3. Verify all files are uploaded correctly
4. Ensure the virtual environment is activated

### Success Indicators

✅ **Deployment successful when:**
- Site loads without errors
- Login page appears
- Can log in with admin/admin123
- Barangay dropdown shows 29 options
- Can create waste items
- Dashboard shows statistics
