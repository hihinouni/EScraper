// Global variables
let eventSource = null;
let isRunning = false;

// DOM elements
const urlInput = document.getElementById('url-input');
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const clearBtn = document.getElementById('clear-btn');
const statusText = document.getElementById('status-text');
const terminal = document.getElementById('terminal');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkStatus();
    setInterval(checkStatus, 2000); // Check status every 2 seconds
});

// Start scraping
startBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    
    if (!url) {
        addTerminalLine('error', 'Please enter a URL');
        return;
    }
    
    // Validate URL
    try {
        new URL(url);
    } catch (e) {
        addTerminalLine('error', 'Invalid URL format');
        return;
    }
    
    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addTerminalLine('info', `Starting scraper for: ${url}`);
            addTerminalLine('info', 'Connecting to server...');
            startEventStream();
            updateUI(true);
        } else {
            addTerminalLine('error', data.message || 'Failed to start scraper');
        }
    } catch (error) {
        addTerminalLine('error', `Error: ${error.message}`);
    }
});

// Stop scraping
stopBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/api/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addTerminalLine('info', 'Stop signal sent...');
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
        } else {
            addTerminalLine('error', data.message || 'Failed to stop scraper');
        }
    } catch (error) {
        addTerminalLine('error', `Error: ${error.message}`);
    }
});

// Clear terminal
clearBtn.addEventListener('click', () => {
    terminal.innerHTML = '';
    addTerminalLine('welcome', 'Terminal cleared');
});

// Start event stream
function startEventStream() {
    if (eventSource) {
        eventSource.close();
    }
    
    eventSource = new EventSource('/api/stream');
    
    eventSource.onmessage = (event) => {
        const data = event.data;
        
        if (data === '__SCRAPER_FINISHED__') {
            eventSource.close();
            eventSource = null;
            updateUI(false);
            addTerminalLine('success', '\n✓ Scraping finished');
            return;
        }
        
        if (data.trim()) {
            // Determine line type based on content
            let lineType = 'info';
            if (data.includes('Error') || data.includes('✗') || data.includes('error')) {
                lineType = 'error';
            } else if (data.includes('✓') || data.includes('Found') || data.includes('Saved')) {
                lineType = 'success';
            } else if (data.includes('Checking') || data.includes('Parsing')) {
                lineType = 'info';
            }
            
            addTerminalLine(lineType, data);
        }
    };
    
    eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        if (eventSource.readyState === EventSource.CLOSED) {
            updateUI(false);
        }
    };
}

// Add line to terminal
function addTerminalLine(type, text) {
    const line = document.createElement('div');
    line.className = `terminal-line ${type} new`;
    
    // Remove new class after animation
    setTimeout(() => {
        line.classList.remove('new');
    }, 300);
    
    // Format text - handle escaped newlines
    const formattedText = text.replace(/\\n/g, '\n');
    
    // Check if it starts with a prompt-like pattern
    if (formattedText.match(/^[=]+$/)) {
        // Separator line
        line.innerHTML = `<span class="text">${escapeHtml(formattedText)}</span>`;
    } else if (formattedText.includes('\n')) {
        // Multi-line text
        const lines = formattedText.split('\n');
        line.innerHTML = lines.map(l => 
            l.trim() ? `<span class="text">${escapeHtml(l)}</span>` : ''
        ).join('<br>');
    } else {
        line.innerHTML = `<span class="text">${escapeHtml(formattedText)}</span>`;
    }
    
    terminal.appendChild(line);
    
    // Auto-scroll to bottom
    terminal.scrollTop = terminal.scrollHeight;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Update UI state
function updateUI(running) {
    isRunning = running;
    startBtn.disabled = running;
    stopBtn.disabled = !running;
    urlInput.disabled = running;
    
    if (running) {
        statusText.textContent = '● Running';
        statusText.className = 'status running';
    } else {
        statusText.textContent = '● Stopped';
        statusText.className = 'status stopped';
    }
}

// Check status
async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.is_running && !isRunning) {
            // Scraper started externally or page refreshed
            updateUI(true);
            if (!eventSource) {
                startEventStream();
            }
        } else if (!data.is_running && isRunning) {
            // Scraper stopped
            updateUI(false);
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
        }
    } catch (error) {
        console.error('Status check error:', error);
    }
}

// Allow Enter key to start
urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !startBtn.disabled) {
        startBtn.click();
    }
});

