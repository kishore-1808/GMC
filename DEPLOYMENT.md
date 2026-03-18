# GLOBAL DEPLOYMENT GUIDE

## Option 1: NGROK (Quick - Free)

### Step 1: Install ngrok
1. Go to: https://ngrok.com/download
2. Download Windows version
3. Extract to a folder
4. Add to PATH or use full path

### Step 2: Run the application
```bash
cd "C:\Users\kishore\Desktop\hospitalmanagement\New folder\New folder (2)\website"

# Start Flask server in one terminal
python app.py

# In another terminal, start ngrok
ngrok http 5000
```

### Step 3: Get Public URL
- ngrok will show a URL like: `https://xxxx.ngrok.io`
- Share this URL with anyone!
- Performance: Good for testing, fair for production

---

## Option 2: PythonAnywhere (Permanent - Free)

### Step 1: Create Account
1. Go to: https://www.pythonanywhere.com/
2. Create free account

### Step 2: Upload Files
1. Upload these files to PythonAnywhere:
   - app.py
   - templates/index.html

### Step 3: Create Web App
1. Go to Web tab
2. Add new web app
3. Select Flask and Python 3.9+
4. Files will be in: /home/username/yourapp/

### Step 4: Configure
- Edit app.py path in web config
- Set to: /home/username/yourapp/app.py

### Step 5: Access
- Your app will be at: https://yourusername.pythonanywhere.com

---

## Option 3: Render (Permanent - Free)

### Step 1: Create Account
1. Go to: https://render.com/
2. Sign up with GitHub

### Step 2: Deploy
1. Create new Web Service
2. Connect your GitHub repository
3. Set build command: pip install -r requirements.txt
4. Set start command: gunicorn app:app

---

## Option 4: Local Network Access

To access from phone/laptop on same WiFi:

```bash
# Find your IP
ipconfig
# Look for IPv4 Address (e.g., 192.168.1.100)

# On other devices, open:
http://192.168.1.100:5000
```

---

## RECOMMENDED: For Best Performance

For real-time video streaming globally, I recommend:

1. **ngrok** - Quick testing, reasonable performance
2. **PythonAnywhere** - Permanent, free tier works well

---

## Troubleshooting

### Camera not working on cloud?
- Cloud servers don't have webcam access
- You need to run locally with ngrok tunneling

### Slow video?
- Reduce video quality in app.py
- Use local network for best speed

### Port already in use?
```bash
# Kill existing process
netstat -ano | findstr :5000
taskkill /F /PID <PID>
```
