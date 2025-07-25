import { createServer } from 'http';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = 3000;

const mimeTypes = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json'
};

const server = createServer((req, res) => {
  // 设置CORS头部
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  let filePath = req.url;
  
  // 路由处理
  if (req.url === '/') {
    filePath = '/test.html';
  } else if (req.url === '/memory') {
    filePath = '/test-memory.html';
  } else if (req.url === '/agent') {
    filePath = '/test-agent.html';
  }
  
  filePath = join(__dirname, filePath);

  try {
    const content = readFileSync(filePath);
    const ext = filePath.substring(filePath.lastIndexOf('.'));
    const contentType = mimeTypes[ext] || 'text/plain';
    
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(content);
  } catch (error) {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('File not found');
  }
});

server.listen(PORT, () => {
  console.log(`🚀 Test server running at http://localhost:${PORT}`);
  console.log('');
  console.log('📄 Available Routes:');
  console.log(`  🔗 LLM Client Test:    http://localhost:${PORT}/`);
  console.log(`  🧠 Memory System Test: http://localhost:${PORT}/memory`);
  console.log(`  🤖 Agent System Test:  http://localhost:${PORT}/agent`);
  console.log('');
  console.log('💡 Open your browser and navigate to the URLs above');
});