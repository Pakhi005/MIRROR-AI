const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

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
    // data: { targetSocketId, roomUrl }
    const { targetSocketId, roomUrl } = data;
    // Send the room URL back to User A
    io.to(targetSocketId).emit('request-accepted', { roomUrl });
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

// Create a Daily.co room
app.post('/create-room', async (req, res) => {
  const DAILY_API_KEY = process.env.DAILY_API_KEY;
  
  if (!DAILY_API_KEY) {
    // Fallback if no API key is provided
    console.log("No Daily API Key found. Returning fallback room.");
    return res.json({ url: "https://c.daily.co/demo" }); // fallback dummy
  }

  try {
    const response = await fetch("https://api.daily.co/v1/rooms", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${DAILY_API_KEY}`
      },
      body: JSON.stringify({
        properties: {
          exp: Math.round(Date.now() / 1000) + 3600, // Expires in 1 hour
        }
      })
    });
    
    const room = await response.json();
    if (room.url) {
      return res.json({ url: room.url });
    } else {
      throw new Error(room.error || "Failed to create room");
    }
  } catch (error) {
    console.error("Error creating daily room:", error);
    // Fallback on error
    return res.json({ url: "https://c.daily.co/demo" });
  }
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Node server running on port ${PORT}`);
});
