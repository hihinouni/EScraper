# Website Scraper - Offline Website Creator

A Python scraper with a beautiful web interface that downloads entire websites for offline viewing. Creates a single index page linking to all downloaded pages.

## What It Does

This scraper downloads **entire websites** for offline viewing:

1. **Discovers URLs** from sitemaps (robots.txt, common locations)
2. **Downloads all web pages** from the discovered URLs
3. **Saves HTML files** locally with proper directory structure
4. **Creates a single index page** (`index.html`) that links to all downloaded pages
5. **Fixes internal links** to work offline

### Output Structure

```
offline_website/
├── index.html          # Main index page with all links
├── pages/              # All downloaded HTML pages
│   ├── page1.html
│   ├── page2.html
│   └── ...
└── scrape_report.json  # Detailed report of the scraping process
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Web Interface (Recommended)

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Enter any URL from the website you want to scrape (e.g., `https://quran.com` or `https://quran.com/al-baqarah`)
4. (Optional) Set a maximum number of pages to download (useful for testing)
5. Click "Start Scraping" to begin
6. Watch the real-time terminal output as pages are downloaded
7. Click "Stop Scraping" to stop at any time
8. Once complete, open `offline_website/index.html` in your browser to view the offline website

### Command Line Interface

You can also run the scraper directly from the command line:

```python
from website_scraper import WebsiteScraper

scraper = WebsiteScraper("https://example.com", max_pages=100)
scraper.scrape_website()
```

## Output

- **Offline Website**: All downloaded pages are saved in the `offline_website/pages/` directory
- **Index Page**: A beautiful index page at `offline_website/index.html` with:
  - Search functionality
  - Statistics (total pages, failed downloads)
  - Links to all downloaded pages
  - Organized by page title
- **Report**: A JSON report (`offline_website/scrape_report.json`) containing:
  - All downloaded URLs
  - Page titles and file paths
  - Failed URLs
  - Statistics summary

## Features

### Web Interface
- 🎨 Beautiful, modern UI with gradient design
- 📺 Real-time terminal output using Server-Sent Events (SSE)
- ▶️ Start/Stop controls for scraping process
- 🗑️ Clear terminal button
- 📊 Status indicators (Running/Stopped)
- 📱 Responsive design for mobile devices

### Scraper
- ✅ Automatically discovers URLs from sitemaps
- ✅ Downloads actual web pages (not just sitemaps)
- ✅ Creates offline website with working internal links
- ✅ Generates beautiful index page with search
- ✅ Respects rate limits (0.5 second delay between requests)
- ✅ Handles errors gracefully
- ✅ Stop functionality for graceful termination
- ✅ Optional page limit for testing
- ✅ Fixes relative links to work offline

## Notes

- The scraper includes a 0.5-second delay between requests to be respectful to the server
- All pages are saved as HTML files in the `offline_website/pages/` directory
- Internal links are automatically fixed to work offline
- External links open in new tabs
- The index page includes search functionality to quickly find pages
- Use the "Max Pages" option to limit downloads for testing purposes

