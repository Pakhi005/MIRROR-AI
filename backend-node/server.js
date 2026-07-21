const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

// Serve static files from the frontend directory
app.use(express.static(path.join(__dirname, '../frontend')));

const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// In-memory store for online users
// Format: { socketId: { name, domain, year, socketId } }
let onlineUsers = {};

io.on('connection', (socket) => {
  console.log(`User connected: ${socket.id}`);

  // When a user joins the peer page
  socket.on('join', (userData) => {
    onlineUsers[socket.id] = { ...userData, socketId: socket.id };
    // Broadcast updated list to everyone
    io.emit('online-users', Object.values(onlineUsers));
  });

  // When User A requests to connect with User B
  socket.on('connect-request', (data) => {
    // data: { targetSocketId, fromName, fromDomain }
    const { targetSocketId, fromName, fromDomain } = data;
    if (onlineUsers[targetSocketId]) {
      io.to(targetSocketId).emit('receive-request', {
        fromSocketId: socket.id,
        fromName,
        fromDomain
      });
    }
  });

  // When User B accepts the request
  socket.on('connect-accepted', (data) => {
    // data: { targetSocketId }
    const { targetSocketId } = data;
    io.to(targetSocketId).emit('request-accepted', { fromSocketId: socket.id });
  });

  // When User B declines the request
  socket.on('connect-declined', (data) => {
    const { targetSocketId } = data;
    io.to(targetSocketId).emit('request-declined');
  });

  // WebRTC Signaling
  socket.on('webrtc-offer', (data) => {
    io.to(data.targetSocketId).emit('webrtc-offer', {
      sdp: data.sdp,
      fromSocketId: socket.id
    });
  });

  socket.on('webrtc-answer', (data) => {
    io.to(data.targetSocketId).emit('webrtc-answer', {
      sdp: data.sdp,
      fromSocketId: socket.id
    });
  });

  socket.on('webrtc-ice-candidate', (data) => {
    io.to(data.targetSocketId).emit('webrtc-ice-candidate', {
      candidate: data.candidate,
      fromSocketId: socket.id
    });
  });

  socket.on('call-ended', (data) => {
    io.to(data.targetSocketId).emit('call-ended');
  });

  socket.on('disconnect', () => {
    console.log(`User disconnected: ${socket.id}`);
    delete onlineUsers[socket.id];
    io.emit('online-users', Object.values(onlineUsers));
  });
});

app.get('/', (req, res) => {
  res.json({ message: 'Hello from Node.js Backend!' });
});

app.get('/online-users', (req, res) => {
  res.json(Object.values(onlineUsers));
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Node server running on port ${PORT}`);
});
