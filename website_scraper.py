"""
Website Scraper - Downloads entire website for offline viewing
Creates a single index page linking to all downloaded pages
"""

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse, unquote
import os
import time
from typing import List, Set, Dict
import json
import re
from pathlib import Path
import html


class WebsiteScraper:
    def __init__(self, base_url: str, stop_callback=None, max_pages=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.stop_callback = stop_callback
        self.max_pages = max_pages  # Limit number of pages to download
        
        # Storage
        self.downloaded_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.pages_data: List[Dict] = []  # Store page info for index
        self.download_dir = "offline_website"
        self.pages_dir = os.path.join(self.download_dir, "pages")
        
        # Create directories
        os.makedirs(self.pages_dir, exist_ok=True)
        
    def get_sitemap_urls(self) -> Set[str]:
        """Get all URLs from sitemaps"""
        print("=" * 60)
        print("Discovering sitemaps and extracting URLs...")
        print("=" * 60)
        
        all_urls = set()
        sitemaps_found = set()
        
        # Check robots.txt
        try:
            robots_url = urljoin(self.base_url, "/robots.txt")
            print(f"\n[1] Checking robots.txt...")
            response = self.session.get(robots_url, timeout=10)
            if response.status_code == 200:
                for line in response.text.split('\n'):
                    if line.lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        sitemaps_found.add(sitemap_url)
                        print(f"  Found sitemap: {sitemap_url}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Check common locations
        common_paths = ["/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml"]
        for path in common_paths:
            try:
                url = urljoin(self.base_url, path)
                response = self.session.head(url, timeout=10)
                if response.status_code == 200:
                    sitemaps_found.add(url)
                    print(f"  Found sitemap: {url}")
            except:
                pass
        
        # Extract URLs from sitemaps
        print(f"\n[2] Extracting URLs from {len(sitemaps_found)} sitemap(s)...")
        for sitemap_url in sitemaps_found:
            if self.stop_callback and self.stop_callback():
                break
            try:
                urls = self._extract_urls_from_sitemap(sitemap_url)
                all_urls.update(urls)
                print(f"  Extracted {len(urls)} URLs from {sitemap_url}")
            except Exception as e:
                print(f"  Error extracting from {sitemap_url}: {e}")
        
        # Filter URLs to only include pages from the base domain
        filtered_urls = {url for url in all_urls if urlparse(url).netloc == urlparse(self.base_url).netloc}
        
        print(f"\n[3] Found {len(filtered_urls)} total URLs from {self.base_url}")
        return filtered_urls
    
    def _extract_urls_from_sitemap(self, sitemap_url: str) -> Set[str]:
        """Extract URLs from a sitemap XML file"""
        urls = set()
        try:
            response = self.session.get(sitemap_url, timeout=30)
            root = ET.fromstring(response.content)
            
            # Handle sitemap index
            if root.tag.endswith('sitemapindex'):
                namespace = {'ns': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}
                for sitemap in root.findall('.//ns:sitemap', namespace) if namespace else root.findall('.//sitemap'):
                    loc = sitemap.find('ns:loc', namespace) if namespace else sitemap.find('loc')
                    if loc is not None:
                        nested_urls = self._extract_urls_from_sitemap(loc.text)
                        urls.update(nested_urls)
            
            # Handle URL set
            elif root.tag.endswith('urlset'):
                namespace = {'ns': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}
                for url_elem in root.findall('.//ns:url', namespace) if namespace else root.findall('.//url'):
                    loc = url_elem.find('ns:loc', namespace) if namespace else url_elem.find('loc')
                    if loc is not None:
                        urls.add(loc.text)
        except Exception as e:
            print(f"    Error parsing sitemap: {e}")
        
        return urls
    
    def sanitize_filename(self, url: str) -> str:
        """Convert URL to a safe filename"""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if not path:
            path = "index"
        
        # Replace invalid characters
        path = re.sub(r'[<>:"|?*]', '_', path)
        path = path.replace('/', '_')
        path = unquote(path)  # Decode URL encoding
        
        # Limit length
        if len(path) > 200:
            path = path[:200]
        
        # Add extension if needed
        if not path.endswith('.html'):
            path += '.html'
        
        return path
    
    def download_page(self, url: str) -> bool:
        """Download a single page and save it"""
        if url in self.downloaded_urls:
            return True
        
        if self.stop_callback and self.stop_callback():
            return False
        
        try:
            print(f"Downloading: {url}")
            response = self.session.get(url, timeout=30, allow_redirects=True)
            
            if response.status_code != 200:
                print(f"  Failed: HTTP {response.status_code}")
                self.failed_urls.add(url)
                return False
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Fix relative links to point to local files
            self._fix_links(soup, url)
            
            # Get page title
            title = soup.find('title')
            page_title = title.get_text().strip() if title else url
            
            # Save HTML
            filename = self.sanitize_filename(url)
            filepath = os.path.join(self.pages_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            # Store page info for index
            self.pages_data.append({
                'url': url,
                'title': page_title,
                'filename': filename,
                'filepath': f"pages/{filename}"
            })
            
            self.downloaded_urls.add(url)
            print(f"  ✓ Saved: {filename}")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.failed_urls.add(url)
            return False
    
    def _fix_links(self, soup: BeautifulSoup, current_url: str):
        """Fix links in HTML to point to local files"""
        base_domain = urlparse(self.base_url).netloc
        
        # Fix <a> tags
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            absolute_url = urljoin(current_url, href)
            parsed = urlparse(absolute_url)
            
            # Only fix links to the same domain
            if parsed.netloc == base_domain:
                filename = self.sanitize_filename(absolute_url)
                tag['href'] = f"pages/{filename}"
            else:
                # External links - keep as is but mark
                tag['target'] = '_blank'
                tag['rel'] = 'noopener noreferrer'
        
        # Fix <img> tags - keep as absolute URLs for now (could download later)
        # Fix <link> tags for CSS
        for tag in soup.find_all('link', href=True):
            href = tag['href']
            absolute_url = urljoin(current_url, href)
            parsed = urlparse(absolute_url)
            if parsed.netloc == base_domain:
                # Could download CSS files here if needed
                pass
        
        # Fix <script> tags
        for tag in soup.find_all('script', src=True):
            src = tag['src']
            absolute_url = urljoin(current_url, src)
            parsed = urlparse(absolute_url)
            if parsed.netloc == base_domain:
                # Could download JS files here if needed
                pass
    
    def create_index_page(self):
        """Create a single index page with links to all downloaded pages"""
        print(f"\n{'=' * 60}")
        print("Creating index page...")
        print(f"{'=' * 60}")
        
        # Sort pages by title
        sorted_pages = sorted(self.pages_data, key=lambda x: x['title'].lower())
        
        # Generate HTML
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Offline Website Index - {self.base_url}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        header p {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .stats {{
            padding: 20px 40px;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .search-box {{
            padding: 20px 40px;
            background: white;
            border-bottom: 1px solid #e0e0e0;
        }}
        #search-input {{
            width: 100%;
            padding: 12px 16px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
        }}
        #search-input:focus {{
            outline: none;
            border-color: #667eea;
        }}
        .pages-list {{
            padding: 20px 40px;
            max-height: 600px;
            overflow-y: auto;
        }}
        .page-item {{
            padding: 15px;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            transition: all 0.3s;
        }}
        .page-item:hover {{
            background: #e9ecef;
            transform: translateX(5px);
        }}
        .page-item.hidden {{
            display: none;
        }}
        .page-title {{
            font-size: 1.1em;
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }}
        .page-link {{
            color: #667eea;
            text-decoration: none;
            font-size: 0.9em;
        }}
        .page-link:hover {{
            text-decoration: underline;
        }}
        .page-url {{
            color: #999;
            font-size: 0.85em;
            font-family: monospace;
            word-break: break-all;
        }}
        footer {{
            padding: 20px 40px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 Offline Website</h1>
            <p>{self.base_url}</p>
        </header>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{len(self.downloaded_urls)}</div>
                <div class="stat-label">Pages Downloaded</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(self.failed_urls)}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(sorted_pages)}</div>
                <div class="stat-label">Total Pages</div>
            </div>
        </div>
        
        <div class="search-box">
            <input type="text" id="search-input" placeholder="Search pages...">
        </div>
        
        <div class="pages-list" id="pages-list">
"""
        
        for page in sorted_pages:
            safe_title = html.escape(page['title'])
            safe_url = html.escape(page['url'])
            safe_filepath = html.escape(page['filepath'])
            
            html_content += f"""
            <div class="page-item" data-title="{safe_title.lower()}" data-url="{safe_url.lower()}">
                <div class="page-title">{safe_title}</div>
                <a href="{safe_filepath}" class="page-link" target="_blank">{safe_filepath}</a>
                <div class="page-url">{safe_url}</div>
            </div>
"""
        
        html_content += """
        </div>
        
        <footer>
            <p>Generated on """ + time.strftime("%Y-%m-%d %H:%M:%S") + """</p>
        </footer>
    </div>
    
    <script>
        const searchInput = document.getElementById('search-input');
        const pageItems = document.querySelectorAll('.page-item');
        
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            
            pageItems.forEach(item => {
                const title = item.getAttribute('data-title');
                const url = item.getAttribute('data-url');
                
                if (title.includes(searchTerm) || url.includes(searchTerm)) {
                    item.classList.remove('hidden');
                } else {
                    item.classList.add('hidden');
                }
            });
        });
    </script>
</body>
</html>
"""
        
        # Save index page
        index_path = os.path.join(self.download_dir, "index.html")
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Index page created: {index_path}")
        print(f"  Total pages: {len(sorted_pages)}")
    
    def scrape_website(self):
        """Main method to scrape the entire website"""
        print("=" * 60)
        print(f"Starting website scrape: {self.base_url}")
        print("=" * 60)
        
        # Step 1: Get URLs from sitemaps
        urls = self.get_sitemap_urls()
        
        if not urls:
            print("\n⚠ No URLs found in sitemaps. Trying to scrape from homepage...")
            urls = {self.base_url}
        
        # Limit URLs if max_pages is set
        if self.max_pages:
            urls = list(urls)[:self.max_pages]
            print(f"\n⚠ Limited to {self.max_pages} pages")
        
        # Step 2: Download pages
        print(f"\n{'=' * 60}")
        print(f"Downloading {len(urls)} pages...")
        print(f"{'=' * 60}\n")
        
        total = len(urls)
        for i, url in enumerate(urls, 1):
            if self.stop_callback and self.stop_callback():
                print("\n⚠ Stop signal received")
                break
            
            print(f"[{i}/{total}] ", end="")
            self.download_page(url)
            time.sleep(0.5)  # Be respectful with requests
        
        # Step 3: Create index page
        if self.pages_data:
            self.create_index_page()
        
        # Step 4: Generate report
        self.generate_report()
        
        print(f"\n{'=' * 60}")
        print("SCRAPING COMPLETE")
        print(f"{'=' * 60}")
        print(f"Downloaded: {len(self.downloaded_urls)} pages")
        print(f"Failed: {len(self.failed_urls)} pages")
        print(f"Index page: offline_website/index.html")
        print(f"{'=' * 60}")
    
    def generate_report(self):
        """Generate a JSON report"""
        report = {
            'base_url': self.base_url,
            'total_pages': len(self.pages_data),
            'downloaded': len(self.downloaded_urls),
            'failed': len(self.failed_urls),
            'failed_urls': list(self.failed_urls),
            'pages': self.pages_data,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        report_path = os.path.join(self.download_dir, "scrape_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Report saved: {report_path}")

