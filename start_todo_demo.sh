#!/bin/bash

# Define path to the app directory
APP_DIR="./app_project_1746588204_web"
cd "$APP_DIR"

# Create a demo .env file that skips real database connections
cat > .env << EOL
# Server Configuration
PORT=3000

# Database Configuration (Demo mode)
DB_DEMO_MODE=true

# Other Configuration
NODE_ENV=development
EOL

# Install dependencies if needed
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules/.package-json-check" ]; then
    echo "[INFO] Installing dependencies..."
    npm install
    touch node_modules/.package-json-check
fi

# Create a temporary server file for demo mode
cat > server_demo.js << EOL
const express = require('express');
const path = require('path');

// Create Express app
const app = express();
const PORT = process.env.PORT || 3000;

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());

// Demo data
const todos = [
  { id: 1, title: 'Buy groceries', completed: false, description: 'Get milk, eggs, and bread' },
  { id: 2, title: 'Go to the gym', completed: true, description: 'Cardio and strength training' },
  { id: 3, title: 'Work on project', completed: false, description: 'Finish the presentation slides' }
];

// API routes for demo
app.get('/api/todos', (req, res) => {
  res.json(todos);
});

app.post('/api/todos', (req, res) => {
  const newTodo = { 
    id: todos.length + 1, 
    title: req.body.title, 
    description: req.body.description || '',
    completed: false 
  };
  todos.push(newTodo);
  res.status(201).json(newTodo);
});

app.put('/api/todos/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const todoIndex = todos.findIndex(t => t.id === id);
  
  if (todoIndex === -1) {
    return res.status(404).json({ error: 'Todo not found' });
  }
  
  todos[todoIndex] = { ...todos[todoIndex], ...req.body };
  res.json(todos[todoIndex]);
});

app.delete('/api/todos/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const todoIndex = todos.findIndex(t => t.id === id);
  
  if (todoIndex === -1) {
    return res.status(404).json({ error: 'Todo not found' });
  }
  
  const deletedTodo = todos.splice(todoIndex, 1)[0];
  res.json(deletedTodo);
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'UP', mode: 'DEMO' });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(\`[DEMO MODE] Server running on http://0.0.0.0:\${PORT}\`);
  console.log('[DEMO MODE] This version uses in-memory data and does not require a database');
  console.log('[DEMO MODE] All data will be lost when the server is restarted');
});
EOL

# Ensure the app binds to 0.0.0.0 to allow connections from Windows host
echo "[INFO] Starting Todo app DEMO MODE on 0.0.0.0:3000..."
echo "[INFO] This is a demo without a real database connection"
echo "[INFO] You can now access the app from your Windows browser at http://localhost:3000"

# Start the app in demo mode
node server_demo.js

echo "[INFO] App stopped."