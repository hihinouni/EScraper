# Sitemap Scraper - Web Interface

A Python scraper with a beautiful web interface that discovers and downloads all sitemaps from any website.

## What Was Found

The scraper successfully discovered and downloaded **all sitemaps** from quran.com:

- **Main Sitemap Index**: `sitemap.xml` (contains references to 9 nested sitemaps)
- **9 Nested Sitemaps**: `sitemap-0.xml` through `sitemap-8.xml`
- **Total URLs**: 166,271 URLs across all sitemaps

### Sitemap Structure

```
sitemap.xml (index)
├── sitemap-0.xml (20,000 URLs)
├── sitemap-1.xml (20,000 URLs)
├── sitemap-2.xml (20,000 URLs)
├── sitemap-3.xml (20,000 URLs)
├── sitemap-4.xml (20,000 URLs)
├── sitemap-5.xml (20,000 URLs)
├── sitemap-6.xml (20,000 URLs)
├── sitemap-7.xml (20,000 URLs)
└── sitemap-8.xml (6,271 URLs)
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
4. Click "Start Scraping" to begin
5. Watch the real-time terminal output
6. Click "Stop Scraping" to stop at any time

### Command Line Interface

You can also run the scraper directly from the command line:

```bash
python sitemap_scraper.py
```

The scraper will:
1. Check `robots.txt` for sitemap references
2. Check common sitemap locations (`/sitemap.xml`, `/sitemap_index.xml`, etc.)
3. Check for HTML sitemap pages
4. Download all discovered sitemaps recursively
5. Save all sitemaps to the `sitemaps/` directory
6. Generate a detailed report in `sitemap_report.json`

## Output

- **Sitemaps**: All XML sitemap files are saved in the `sitemaps/` directory
- **Report**: A JSON report (`sitemap_report.json`) containing:
  - Total number of sitemaps
  - Type of each sitemap (index vs urlset)
  - List of all URLs found
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
- ✅ Automatically discovers sitemaps from multiple sources
- ✅ Handles sitemap index files recursively
- ✅ Respects rate limits (1 second delay between requests)
- ✅ Saves all sitemaps locally
- ✅ Generates comprehensive reports
- ✅ Error handling and logging
- ✅ Stop functionality for graceful termination

## Notes

- The scraper includes a 1-second delay between requests to be respectful to the server
- All sitemaps are saved as XML files for easy parsing
- The report file can be very large (166K+ URLs) but is useful for analysis

