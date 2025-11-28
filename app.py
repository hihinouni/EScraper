"""
Flask backend server for Website Scraper Web Interface
"""

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import threading
import queue
import sys
from io import StringIO
from website_scraper import WebsiteScraper
from urllib.parse import urlparse
import time

app = Flask(__name__)
CORS(app)

# Global variables for scraper control
scraper_thread = None
scraper_instance = None
output_queue = queue.Queue()
is_running = False
should_stop = False


class StreamOutput:
    """Capture print statements and send to queue"""
    def __init__(self, queue_obj):
        self.queue = queue_obj
        self.original_stdout = sys.stdout
        
    def write(self, text):
        if text.strip():  # Only send non-empty lines
            self.queue.put(text)
        self.original_stdout.write(text)
        self.original_stdout.flush()
        
    def flush(self):
        self.original_stdout.flush()


def extract_base_url(url):
    """Extract base URL from any URL"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def run_scraper(base_url, max_pages=None):
    """Run the scraper in a separate thread"""
    global scraper_instance, is_running, should_stop
    
    try:
        is_running = True
        should_stop = False
        
        # Create stream output handler
        stream = StreamOutput(output_queue)
        sys.stdout = stream
        
        # Create scraper instance with stop callback
        scraper_instance = WebsiteScraper(base_url, stop_callback=lambda: should_stop, max_pages=max_pages)
        
        # Scrape the entire website
        scraper_instance.scrape_website()
        
        if not should_stop:
            output_queue.put("\n✓ Website scraping completed successfully!\n")
            output_queue.put(f"✓ Index page created at: offline_website/index.html\n")
        else:
            output_queue.put("\n⚠ Scraping stopped by user\n")
            
    except Exception as e:
        output_queue.put(f"\n✗ Error: {str(e)}\n")
        import traceback
        output_queue.put(traceback.format_exc())
    finally:
        sys.stdout = sys.__stdout__
        is_running = False
        output_queue.put("__SCRAPER_FINISHED__")


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/start', methods=['POST'])
def start_scraper():
    """Start the scraper"""
    global scraper_thread, is_running, should_stop
    
    if is_running:
        return jsonify({'status': 'error', 'message': 'Scraper is already running'}), 400
    
    data = request.json
    url = data.get('url', '').strip()
    max_pages = data.get('max_pages', None)  # Optional limit
    
    if not url:
        return jsonify({'status': 'error', 'message': 'URL is required'}), 400
    
    # Extract base URL
    try:
        base_url = extract_base_url(url)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Invalid URL: {str(e)}'}), 400
    
    # Convert max_pages to int if provided
    if max_pages:
        try:
            max_pages = int(max_pages)
        except:
            max_pages = None
    
    # Clear the queue
    while not output_queue.empty():
        try:
            output_queue.get_nowait()
        except:
            pass
    
    should_stop = False
    scraper_thread = threading.Thread(target=run_scraper, args=(base_url, max_pages), daemon=True)
    scraper_thread.start()
    
    return jsonify({'status': 'success', 'message': 'Website scraper started'})


@app.route('/api/stop', methods=['POST'])
def stop_scraper():
    """Stop the scraper"""
    global should_stop, is_running
    
    if not is_running:
        return jsonify({'status': 'error', 'message': 'Scraper is not running'}), 400
    
    should_stop = True
    output_queue.put("\n⚠ Stopping scraper...\n")
    
    return jsonify({'status': 'success', 'message': 'Stop signal sent'})


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get scraper status"""
    return jsonify({
        'status': 'running' if is_running else 'stopped',
        'is_running': is_running
    })


@app.route('/api/stream')
def stream():
    """Stream scraper output"""
    def generate():
        while True:
            try:
                # Get output from queue with timeout
                try:
                    output = output_queue.get(timeout=1)
                    if output == "__SCRAPER_FINISHED__":
                        yield f"data: {output}\n\n"
                        break
                    # Escape newlines for SSE format
                    output = output.replace('\n', '\\n').replace('\r', '')
                    yield f"data: {output}\n\n"
                except queue.Empty:
                    # Send heartbeat to keep connection alive
                    yield f"data: \n\n"
                    continue
            except Exception as e:
                yield f"data: Error: {str(e)}\n\n"
                break
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


if __name__ == '__main__':
    print("Starting Flask server...")
    print("Open http://localhost:5000 in your browser")
    print("This will scrape entire websites and create an offline index page")
    app.run(debug=True, threaded=True, port=5000)

