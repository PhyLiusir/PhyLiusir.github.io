#!/usr/bin/env python3
"""
Simple HTTP server for local development
"""

import http.server
import socketserver
import os
import webbrowser
import sys

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def main():
    os.chdir(DIRECTORY)

    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"\n🚀 Server running at http://localhost:{PORT}")
            print(f"📁 Serving directory: {DIRECTORY}")
            print("\n📋 Available routes:")
            print("  • http://localhost:8000/          - Main website")
            print("  • http://localhost:8000/css/      - CSS styles")
            print("  • http://localhost:8000/js/       - JavaScript")
            print("\n🛑 Press Ctrl+C to stop the server")
            print("-" * 50)

            # Open browser automatically
            webbrowser.open(f'http://localhost:{PORT}')

            httpd.serve_forever()

    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
        sys.exit(0)
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"\n❌ Port {PORT} is already in use!")
            print("Try another port: python server.py 8080")
            sys.exit(1)
        else:
            raise

if __name__ == "__main__":
    # Allow custom port via command line argument
    if len(sys.argv) > 1:
        try:
            PORT = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)

    main()