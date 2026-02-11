#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install Nginx
apt-get install -y nginx

# Create web directory
mkdir -p /var/www/maze-game

# Create index.html with API URL injected
aws s3 cp s3://static-assets-maze-game/html/index.html /var/www/maze-game/index.html

# Create game.js with API URL injected
cat > /var/www/maze-game/game.js << 'JSEOF'
// Configuration - API URL will be injected by Terraform
const CONFIG = {
    apiUrl: '${api_gateway_url}',
    cellSize: 30,
    colors: {
        wall: '#2c3e50',
        path: '#ecf0f1',
        player: '#3498db',
        exit: '#2ecc71',
        grid: '#bdc3c7'
    }
};

// Game state
let gameState = {
    currentStage: 1,
    totalStages: 10,
    maze: [],
    playerX: 0,
    playerY: 0,
    endX: 0,
    endY: 0,
    moves: 0,
    totalMoves: 0,
    stageStartTime: 0,
    gameStartTime: 0,
    isPlaying: false
};

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

async function initGame() {
    gameState.gameStartTime = Date.now();
    await loadStage(1);
}

async function loadStage(stageNumber) {
    try {
        document.getElementById('loadingMessage').style.display = 'block';
        document.getElementById('canvasContainer').style.display = 'none';
        document.getElementById('errorMessage').style.display = 'none';

        const response = await fetch(`$${CONFIG.apiUrl}/$${stageNumber}`);
        
        if (!response.ok) {
            throw new Error(`HTTP $${response.status}: $${response.statusText}`);
        }

        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to load stage');
        }

        const stageData = data.data;

        gameState.maze = stageData.layout.split('\n').map(line => line.split(''));
        gameState.playerX = stageData.start_x;
        gameState.playerY = stageData.start_y;
        gameState.endX = stageData.end_x;
        gameState.endY = stageData.end_y;
        gameState.currentStage = stageNumber;
        gameState.moves = 0;
        gameState.stageStartTime = Date.now();
        gameState.isPlaying = true;

        document.getElementById('currentStage').textContent = `$${stageNumber}/$${gameState.totalStages}`;
        document.getElementById('moves').textContent = '0';
        
        document.getElementById('loadingMessage').style.display = 'none';
        document.getElementById('canvasContainer').style.display = 'flex';

        renderMaze();

    } catch (error) {
        console.error('Error loading stage:', error);
        showError(`Failed to load stage $${stageNumber}: $${error.message}`);
    }
}

function renderMaze() {
    const maze = gameState.maze;
    const cellSize = CONFIG.cellSize;

    const mazeWidth = maze[0].length * cellSize;
    const mazeHeight = maze.length * cellSize;
    
    canvas.width = mazeWidth;
    canvas.height = mazeHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (let y = 0; y < maze.length; y++) {
        for (let x = 0; x < maze[y].length; x++) {
            const cell = maze[y][x];
            const px = x * cellSize;
            const py = y * cellSize;

            if (cell === '#') {
                ctx.fillStyle = CONFIG.colors.wall;
                ctx.fillRect(px, py, cellSize, cellSize);
                ctx.strokeStyle = CONFIG.colors.grid;
                ctx.strokeRect(px, py, cellSize, cellSize);
            } else {
                ctx.fillStyle = CONFIG.colors.path;
                ctx.fillRect(px, py, cellSize, cellSize);
                ctx.strokeStyle = CONFIG.colors.grid;
                ctx.strokeRect(px, py, cellSize, cellSize);
            }

            if (x === gameState.endX && y === gameState.endY) {
                ctx.fillStyle = CONFIG.colors.exit;
                ctx.fillRect(px, py, cellSize, cellSize);
            }
        }
    }

    const playerPx = gameState.playerX * cellSize + cellSize / 2;
    const playerPy = gameState.playerY * cellSize + cellSize / 2;
    const playerRadius = cellSize / 3;

    ctx.fillStyle = CONFIG.colors.player;
    ctx.beginPath();
    ctx.arc(playerPx, playerPy, playerRadius, 0, Math.PI * 2);
    ctx.fill();
}

document.addEventListener('keydown', (e) => {
    if (!gameState.isPlaying) return;

    let newX = gameState.playerX;
    let newY = gameState.playerY;

    switch(e.key) {
        case 'ArrowUp':
            newY--;
            e.preventDefault();
            break;
        case 'ArrowDown':
            newY++;
            e.preventDefault();
            break;
        case 'ArrowLeft':
            newX--;
            e.preventDefault();
            break;
        case 'ArrowRight':
            newX++;
            e.preventDefault();
            break;
        default:
            return;
    }

    if (isValidMove(newX, newY)) {
        gameState.playerX = newX;
        gameState.playerY = newY;
        gameState.moves++;
        gameState.totalMoves++;

        document.getElementById('moves').textContent = gameState.moves;

        renderMaze();

        if (newX === gameState.endX && newY === gameState.endY) {
            stageComplete();
        }
    }
});

function isValidMove(x, y) {
    const maze = gameState.maze;
    
    if (y < 0 || y >= maze.length) return false;
    if (x < 0 || x >= maze[y].length) return false;
    
    return maze[y][x] !== '#';
}

function stageComplete() {
    gameState.isPlaying = false;

    const stageTime = ((Date.now() - gameState.stageStartTime) / 1000).toFixed(1);

    document.getElementById('stageCompleteMessage').innerHTML = 
        `You completed Stage $${gameState.currentStage}!<br>` +
        `Time: $${stageTime}s | Moves: $${gameState.moves}`;

    if (gameState.currentStage >= gameState.totalStages) {
        gameComplete();
    } else {
        document.getElementById('stageCompleteModal').classList.add('active');
    }
}

function gameComplete() {
    const totalTime = ((Date.now() - gameState.gameStartTime) / 1000).toFixed(1);
    
    document.getElementById('gameCompleteMessage').innerHTML = 
        `You completed all 10 stages!<br><br>` +
        `Total Time: $${totalTime}s<br>` +
        `Total Moves: $${gameState.totalMoves}`;

    document.getElementById('gameCompleteModal').classList.add('active');
}

function continueToNextStage() {
    document.getElementById('stageCompleteModal').classList.remove('active');
    loadStage(gameState.currentStage + 1);
}

function restartGame() {
    document.getElementById('gameCompleteModal').classList.remove('active');
    gameState.totalMoves = 0;
    gameState.gameStartTime = Date.now();
    loadStage(1);
}

function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorMessage').style.display = 'block';
    document.getElementById('loadingMessage').style.display = 'none';
}

setInterval(() => {
    if (gameState.isPlaying) {
        const elapsed = ((Date.now() - gameState.stageStartTime) / 1000).toFixed(1);
        document.getElementById('time').textContent = elapsed + 's';
    }
}, 100);

window.addEventListener('load', initGame);
JSEOF

# Configure Nginx
cat > /etc/nginx/sites-available/maze-game << 'NGINXEOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /var/www/maze-game;
    index index.html;

    server_name _;

    location / {
        try_files $uri $uri/ =404;
    }

    # Enable gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
NGINXEOF

# Enable site
ln -sf /etc/nginx/sites-available/maze-game /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and restart Nginx
nginx -t
systemctl restart nginx
systemctl enable nginx

echo "Web server setup complete!"
