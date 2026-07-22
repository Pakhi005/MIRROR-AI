const express = require('express');
const http = require('http');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

// Serve static files from the frontend directory
app.use(express.static(path.join(__dirname, '../frontend')));

const server = http.createServer(app);

app.get('/', (req, res) => {
  res.json({ message: 'Hello from Node.js Backend!' });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Node server running on port ${PORT}`);
});
