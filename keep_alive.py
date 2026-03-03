import os
from threading import Thread
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")
        
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
            
    # Silent logging to keep console clean
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get('PORT', 10000))
    server = ThreadingHTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Health check server running on port {port}")
    server.serve_forever()

def ping_server():
    import time
    import urllib.request
    
    port = int(os.environ.get('PORT', 10000))
    # Render assigns the app URL to this environment variable
    render_url = os.environ.get('RENDER_EXTERNAL_URL')
    
    while True:
        try:
            time.sleep(120) # Ping every 2 minutes
            
            if render_url:
                url = f"{render_url}/health"
            else:
                url = f"http://127.0.0.1:{port}/health"
                
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            # Silently ignore ping errors
            pass

def keep_alive():
    t_server = Thread(target=run_server)
    t_server.daemon = True
    t_server.start()
    
    t_ping = Thread(target=ping_server)
    t_ping.daemon = True
    t_ping.start()
