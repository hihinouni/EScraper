# Quick Start Guide

## 🚀 Getting Started in 3 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start the Server
```bash
python app.py
```

You should see:
```
Starting Flask server...
Open http://localhost:5000 in your browser
 * Running on http://127.0.0.1:5000
```

### Step 3: Open in Browser
Open your web browser and go to:
```
http://localhost:5000
```

## 📖 How to Use

1. **Enter URL**: Type any URL from the website you want to scrape
   - Example: `https://quran.com`
   - Example: `https://quran.com/al-baqarah`
   - The scraper will automatically extract the base URL

2. **Start Scraping**: Click the green "Start Scraping" button

3. **Watch Progress**: See real-time output in the terminal view

4. **Stop Anytime**: Click the red "Stop Scraping" button to stop

5. **Clear Terminal**: Click "Clear Terminal" to clear the output

## 📁 Output Files

After scraping completes, you'll find:
- **Sitemaps**: All XML files in the `sitemaps/` directory
- **Report**: Detailed JSON report in `sitemap_report.json`

## 🎨 Features

- ✅ Real-time terminal output
- ✅ Start/Stop controls
- ✅ Beautiful modern UI
- ✅ Works with any website
- ✅ Automatic base URL extraction
- ✅ Responsive design

## 🛠️ Troubleshooting

**Port already in use?**
- Change the port in `app.py` (line 94): `app.run(debug=True, threaded=True, port=5001)`

**Module not found?**
- Make sure you installed all dependencies: `pip install -r requirements.txt`

**Can't connect to server?**
- Make sure the Flask server is running
- Check that port 5000 is not blocked by firewall

