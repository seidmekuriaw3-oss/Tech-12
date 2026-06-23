from http.server import HTTPServer, BaseHTTPRequestHandler

class SemiraFashionHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'''<!DOCTYPE html><html><head>
<title>SEMIRA FASHION</title></head><body>
<h1>SEMIRA FASHION</h1>
<p>Server is running. Please use the main Flask app.</p>
</body></html>''')

if __name__ == '__main__':
    print("Starting SEMIRA FASHION HTTP Server...")
    server = HTTPServer(('0.0.0.0', 5000), SemiraFashionHandler)
    server.serve_forever()
