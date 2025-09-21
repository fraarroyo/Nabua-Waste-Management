# Deployment Guide for E-waste Management System

## 🚀 Quick Deployment Options

### Option 1: Render (Recommended - Free)

1. **Sign up** at [render.com](https://render.com)
2. **Connect GitHub** account
3. **Create New Web Service**:
   - Connect your repository: `fraarroyo/Nabua-Waste-Management`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
4. **Environment Variables** (in Render dashboard):
   - `FLASK_ENV=production`
   - `SECRET_KEY=your-secret-key-here`
5. **Deploy** - Render will automatically build and deploy

### Option 2: Railway

1. **Sign up** at [railway.app](https://railway.app)
2. **Deploy from GitHub**:
   - Select your repository
   - Railway auto-detects Flask app
3. **Add Environment Variables**:
   - `FLASK_ENV=production`
   - `SECRET_KEY=your-secret-key-here`
4. **Deploy** - Railway handles the rest

### Option 3: Heroku

1. **Install Heroku CLI** from [heroku.com](https://devcenter.heroku.com/articles/heroku-cli)
2. **Login**: `heroku login`
3. **Create app**: `heroku create nabua-waste-management`
4. **Set environment variables**:
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set SECRET_KEY=your-secret-key-here
   ```
5. **Deploy**: `git push heroku master`

### Option 4: PythonAnywhere

1. **Sign up** at [pythonanywhere.com](https://pythonanywhere.com)
2. **Create new web app** (Flask)
3. **Upload your code** via Git:
   ```bash
   git clone https://github.com/fraarroyo/Nabua-Waste-Management.git
   ```
4. **Configure WSGI file** to point to your app
5. **Reload** the web app

## 🔧 Pre-deployment Checklist

- [ ] Update `SECRET_KEY` in production
- [ ] Set `FLASK_ENV=production`
- [ ] Configure database (SQLite for simple deployment, PostgreSQL for production)
- [ ] Test locally with production settings
- [ ] Update any hardcoded URLs

## 📝 Environment Variables

Create a `.env` file for local development:
```
FLASK_ENV=development
SECRET_KEY=your-development-secret-key
DATABASE_URL=sqlite:///waste_management.db
```

For production, set these in your hosting platform:
```
FLASK_ENV=production
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

## 🗄️ Database Considerations

- **SQLite**: Good for development and small deployments
- **PostgreSQL**: Recommended for production (available on most platforms)
- **Migration**: Use Flask-Migrate for database schema updates

## 🔒 Security Notes

- Change the default `SECRET_KEY`
- Use environment variables for sensitive data
- Enable HTTPS in production
- Consider adding authentication middleware

## 📊 Monitoring

Most platforms provide:
- Application logs
- Performance metrics
- Error tracking
- Uptime monitoring

## 🆘 Troubleshooting

1. **Build fails**: Check `requirements.txt` for all dependencies
2. **App crashes**: Check logs for error messages
3. **Database issues**: Ensure database URL is correct
4. **Static files**: Make sure templates folder is included

## 🌐 Custom Domain

Most platforms allow custom domains:
1. Purchase domain
2. Configure DNS settings
3. Add domain to hosting platform
4. Enable SSL certificate
