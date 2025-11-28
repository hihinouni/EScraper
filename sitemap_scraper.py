"""
Sitemap Scraper for Quran.com
This script discovers and downloads all sitemaps from quran.com
"""

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import os
import time
from typing import List, Set
import json


class QuranSitemapScraper:
    def __init__(self, base_url: str = "https://quran.com", stop_callback=None):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.found_sitemaps: Set[str] = set()
        self.downloaded_sitemaps: List[dict] = []
        self.stop_callback = stop_callback  # Callback function to check if should stop
        
    def check_robots_txt(self) -> List[str]:
        """Check robots.txt for sitemap references"""
        sitemaps = []
        try:
            robots_url = urljoin(self.base_url, "/robots.txt")
            print(f"Checking robots.txt at: {robots_url}")
            response = self.session.get(robots_url, timeout=10)
            if response.status_code == 200:
                for line in response.text.split('\n'):
                    line = line.strip()
                    if line.lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        sitemaps.append(sitemap_url)
                        print(f"Found sitemap in robots.txt: {sitemap_url}")
        except Exception as e:
            print(f"Error checking robots.txt: {e}")
        return sitemaps
    
    def check_common_sitemap_locations(self) -> List[str]:
        """Check common sitemap locations"""
        common_paths = [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/sitemap-index.xml",
            "/sitemaps.xml",
            "/sitemap1.xml",
            "/sitemap_1.xml",
        ]
        
        found = []
        for path in common_paths:
            url = urljoin(self.base_url, path)
            try:
                print(f"Checking: {url}")
                response = self.session.head(url, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    # Verify it's actually XML
                    content_response = self.session.get(url, timeout=10)
                    if content_response.headers.get('content-type', '').startswith('application/xml') or \
                       content_response.headers.get('content-type', '').startswith('text/xml') or \
                       content_response.text.strip().startswith('<?xml'):
                        found.append(url)
                        print(f"✓ Found sitemap: {url}")
            except Exception as e:
                print(f"  Not found or error: {e}")
                continue
        return found
    
    def check_html_sitemap(self) -> List[str]:
        """Check if there's an HTML sitemap page"""
        sitemaps = []
        try:
            sitemap_url = urljoin(self.base_url, "/sitemap")
            print(f"Checking HTML sitemap at: {sitemap_url}")
            response = self.session.get(sitemap_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Look for links to XML sitemaps
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if 'sitemap' in href.lower() and href.endswith('.xml'):
                        full_url = urljoin(self.base_url, href)
                        sitemaps.append(full_url)
                        print(f"Found sitemap link in HTML: {full_url}")
        except Exception as e:
            print(f"Error checking HTML sitemap: {e}")
        return sitemaps
    
    def parse_sitemap(self, url: str) -> dict:
        """Parse a sitemap XML file"""
        try:
            print(f"\nParsing sitemap: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Save the raw XML
            filename = f"sitemaps/{urlparse(url).path.split('/')[-1] or 'sitemap.xml'}"
            os.makedirs("sitemaps", exist_ok=True)
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"Saved: {filename}")
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Check if it's a sitemap index
            sitemap_info = {
                'url': url,
                'filename': filename,
                'type': None,
                'sitemaps': [],
                'urls': []
            }
            
            # Handle sitemap index (contains other sitemaps)
            if root.tag.endswith('sitemapindex'):
                sitemap_info['type'] = 'sitemapindex'
                namespace = {'ns': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}
                
                for sitemap in root.findall('.//ns:sitemap', namespace) if namespace else root.findall('.//sitemap'):
                    loc = sitemap.find('ns:loc', namespace) if namespace else sitemap.find('loc')
                    if loc is not None:
                        sitemap_url = loc.text
                        sitemap_info['sitemaps'].append(sitemap_url)
                        print(f"  Found nested sitemap: {sitemap_url}")
            
            # Handle regular sitemap (contains URLs)
            elif root.tag.endswith('urlset'):
                sitemap_info['type'] = 'urlset'
                namespace = {'ns': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}
                
                for url_elem in root.findall('.//ns:url', namespace) if namespace else root.findall('.//url'):
                    loc = url_elem.find('ns:loc', namespace) if namespace else url_elem.find('loc')
                    if loc is not None:
                        sitemap_info['urls'].append(loc.text)
                
                print(f"  Found {len(sitemap_info['urls'])} URLs in sitemap")
            
            self.downloaded_sitemaps.append(sitemap_info)
            return sitemap_info
            
        except Exception as e:
            print(f"Error parsing sitemap {url}: {e}")
            return None
    
    def discover_all_sitemaps(self) -> Set[str]:
        """Discover all sitemaps using multiple methods"""
        print("=" * 60)
        print(f"Discovering sitemaps for {self.base_url}")
        print("=" * 60)
        
        all_sitemaps = set()
        
        # Method 1: Check robots.txt
        if self.stop_callback and self.stop_callback():
            return all_sitemaps
        print("\n[1] Checking robots.txt...")
        robots_sitemaps = self.check_robots_txt()
        all_sitemaps.update(robots_sitemaps)
        
        # Method 2: Check common locations
        if self.stop_callback and self.stop_callback():
            return all_sitemaps
        print("\n[2] Checking common sitemap locations...")
        common_sitemaps = self.check_common_sitemap_locations()
        all_sitemaps.update(common_sitemaps)
        
        # Method 3: Check HTML sitemap
        if self.stop_callback and self.stop_callback():
            return all_sitemaps
        print("\n[3] Checking HTML sitemap page...")
        html_sitemaps = self.check_html_sitemap()
        all_sitemaps.update(html_sitemaps)
        
        return all_sitemaps
    
    def download_all_sitemaps(self, sitemap_urls: Set[str] = None):
        """Download all discovered sitemaps recursively"""
        if sitemap_urls is None:
            sitemap_urls = self.discover_all_sitemaps()
        
        if not sitemap_urls:
            print("\nNo sitemaps found!")
            return
        
        print(f"\n{'=' * 60}")
        print(f"Downloading {len(sitemap_urls)} sitemap(s)...")
        print(f"{'=' * 60}\n")
        
        # Download initial sitemaps
        nested_sitemaps = set()
        for sitemap_url in sitemap_urls:
            # Check if should stop
            if self.stop_callback and self.stop_callback():
                print("\n⚠ Stop signal received, stopping scraper...")
                return
            
            if sitemap_url not in self.found_sitemaps:
                self.found_sitemaps.add(sitemap_url)
                info = self.parse_sitemap(sitemap_url)
                if info and info['type'] == 'sitemapindex':
                    nested_sitemaps.update(info['sitemaps'])
                time.sleep(1)  # Be respectful with requests
        
        # Recursively download nested sitemaps
        if nested_sitemaps:
            remaining = nested_sitemaps - self.found_sitemaps
            if remaining:
                print(f"\nFound {len(remaining)} nested sitemap(s), downloading...")
                self.download_all_sitemaps(remaining)
    
    def generate_report(self):
        """Generate a report of all downloaded sitemaps"""
        report = {
            'total_sitemaps': len(self.downloaded_sitemaps),
            'sitemaps': self.downloaded_sitemaps,
            'total_urls': sum(len(s['urls']) for s in self.downloaded_sitemaps),
            'sitemap_indexes': sum(1 for s in self.downloaded_sitemaps if s['type'] == 'sitemapindex'),
            'urlsets': sum(1 for s in self.downloaded_sitemaps if s['type'] == 'urlset')
        }
        
        report_file = "sitemap_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'=' * 60}")
        print("DOWNLOAD SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total sitemaps downloaded: {report['total_sitemaps']}")
        print(f"  - Sitemap indexes: {report['sitemap_indexes']}")
        print(f"  - URL sets: {report['urlsets']}")
        print(f"Total URLs found: {report['total_urls']}")
        print(f"\nReport saved to: {report_file}")
        print(f"Sitemaps saved to: sitemaps/")
        
        return report


def main():
    scraper = QuranSitemapScraper()
    
    try:
        # Discover and download all sitemaps
        scraper.download_all_sitemaps()
        
        # Generate report
        scraper.generate_report()
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

