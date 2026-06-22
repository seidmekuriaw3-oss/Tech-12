from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class EthiosadatHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>Ethiosadat Furniture</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #1a73e8, #0d47a1); color: white; }
        h1 { font-size: 48px; }
        .container { background: white; color: #333; padding: 30px; border-radius: 20px; max-width: 600px; margin: 0 auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🪑 Ethiosadat Furniture</h1>
        <p>✅ Server is running successfully!</p>
        <p>Python 3.13 HTTP Server - Working without Flask</p>
        <hr>
        <p>📞 Contact: 0987 957957</p>
        <p>📍 ወሎ ደሴ ኩታበር, Ethiopia</p>
    </div>
</body>
</html>'''
        self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {args[0]}")

print("=" * 50)
print("🚀 Ethiosadat HTTP Server Starting...")
print("📍 http://127.0.0.1:5000")
print("📍 http://localhost:5000")
print("=" * 50)

try:
    server = HTTPServer(('0.0.0.0', 5000), EthiosadatHandler)
    server.serve_forever()
except KeyboardInterrupt:
    print("\n🛑 Server stopped")
    server.server_close()
