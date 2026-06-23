const http = require('http');

const server = http.createServer((req, res) => {
    res.writeHead(200, {'Content-Type': 'text/html'});
    res.end(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>SEMIRA FASHION</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(135deg, #1a73e8, #0d47a1); }
                .container { background: white; padding: 30px; border-radius: 20px; max-width: 600px; margin: 0 auto; }
                h1 { color: #1a73e8; }
                .phone { color: #1a73e8; font-size: 24px; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>👗 SEMIRA FASHION</h1>
                <p>✅ Server is running!</p>
                <p>የቤት እቃዎች በምቹ ዋጋ | Quality Furniture</p>
                <hr>
                <p>📞 <span class="phone">0987 957957</span></p>
                <p>📍 Addis Ababa, Ethiopia</p>
            </div>
        </body>
        </html>
    `);
});

server.listen(5000, '0.0.0.0', () => {
    console.log('🚀 Ethiosadat Server running at http://127.0.0.1:5000');
});
