# Maze Game - Local-First with Cloud Backend

A Python-based maze game demonstrating **Local-First Architecture** with cloud backend services. Player movements are instant (calculated locally), while level data is fetched from AWS Lambda/API Gateway and game analytics are sent to SQS asynchronously.

## 🏗️ Architecture Overview

### Local-First Design Philosophy

This architecture keeps the cloud components (Terraform, PostgreSQL, SQS) but uses them for what they're best at:

**✅ What's LOCAL (Instant)**
- Player movement and collision detection
- Game rendering and UI
- Real-time gameplay logic

**☁️ What's in the CLOUD (Async)**
- Level data storage (PostgreSQL via Lambda)
- Game analytics and statistics (SQS)
- Level loading (API Gateway)

### Architecture Diagram

```
┌─────────────────┐
│  Python Game    │
│   (Pygame)      │
│                 │
│ • Local moves   │◄──── Instant, no network delay
│ • Collision     │
│ • Rendering     │
└────────┬────────┘
         │
         │ On Level Start
         ├──────────────────►  API Gateway ──► Lambda ──► PostgreSQL
         │                    (Fetch level data)
         │
         │ On Level Complete (Fire & Forget)
         └──────────────────►  SQS Queue
                              (Analytics logging)
```

## 📦 Components

### 1. **AWS Lambda** - Secure Database Gateway
- Function: `get_level_data`
- Retrieves maze layouts from PostgreSQL
- Database credentials stored in Secrets Manager
- Accessible via API Gateway

### 2. **API Gateway** - Public API Endpoint
- REST API: `GET /level/{stage_number}`
- Returns JSON with maze layout
- CORS enabled for browser clients

### 3. **PostgreSQL RDS** - Level Storage
- Stores 10 progressive maze stages
- Not directly accessible by game client
- Secured behind Lambda

### 4. **SQS Queue** - Analytics Pipeline
- Receives game completion events
- Async processing (fire and forget)
- Can be consumed by analytics workers later

### 5. **Python Game Client** - Local-First Gameplay
- Pygame-based UI
- Instant movement calculation
- Fetches levels on demand
- Sends analytics asynchronously

## 🚀 Setup Instructions

### Prerequisites

- AWS Account with CLI configured
- Terraform (v1.0+)
- Python (3.8+)
- PostgreSQL client (for initializing DB)

### Step 1: Build Lambda Package

```bash
cd lambda
chmod +x build.sh
./build.sh
```

This creates `lambda_function.zip` in the `terraform/` directory.

### Step 2: Deploy Infrastructure

```bash
cd terraform

# Configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your DB password

# Deploy
terraform init
terraform plan
terraform apply
```

**Save these outputs:**
- `api_gateway_url` - Your API endpoint
- `sqs_queue_url` - Analytics queue URL
- `game_client_access_key_id` - AWS credentials
- `game_client_secret_access_key` - AWS credentials

### Step 3: Initialize Database

Get a temporary security group rule to access RDS:

```bash
# Get your public IP
MY_IP=$(curl -s ifconfig.me)

# Add temporary ingress rule (do this manually in AWS Console)
# Security Group: maze-game-rds-sg
# Add rule: PostgreSQL (5432) from $MY_IP/32
```

Then run the schema:

```bash
cd database
psql -h <RDS_ENDPOINT> -U mazegameadmin -d mazegame -f schema.sql
```

**Remove the temporary rule after initialization!**

### Step 4: Configure Python App

```bash
cd app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Terraform outputs
```

Your `.env` should look like:

```bash
API_GATEWAY_URL=https://abc123.execute-api.us-east-1.amazonaws.com/prod/level
AWS_REGION=us-east-1
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789/maze-game-analytics
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=xyz...
PLAYER_ID=player_001
```

### Step 5: Run the Game!

```bash
python maze_game.py
```

## 🎮 How It Works

### Level Loading (Cloud → Local)

1. Game starts, calls API: `GET /level/1`
2. API Gateway triggers Lambda function
3. Lambda fetches layout from PostgreSQL
4. JSON response sent back to game
5. Game parses and renders locally

### Gameplay (100% Local)

1. Player presses arrow key
2. **Local** collision detection (instant!)
3. **Local** position update
4. **Local** render
5. No network calls = no lag!

### Level Complete (Local → Cloud, Async)

1. Player reaches exit
2. Calculate time & moves locally
3. Send analytics to SQS (fire & forget)
4. Game doesn't wait for response
5. Continue to next level

## 📊 SQS Message Formats

### Level Complete Event

```json
{
  "event_type": "level_complete",
  "player_id": "player_001",
  "stage_number": 1,
  "time_taken": 45.3,
  "moves_count": 78,
  "timestamp": 1234567890.123
}
```

### Game Complete Event

```json
{
  "event_type": "game_complete",
  "player_id": "player_001",
  "total_time": 623.8,
  "total_moves": 892,
  "timestamp": 1234567890.123
}
```

### Game Start Event

```json
{
  "event_type": "game_start",
  "player_id": "player_001",
  "timestamp": 1234567890.123
}
```

## 🔒 Security

- Database is **NOT** publicly accessible
- Lambda has VPC access to RDS
- Database credentials in Secrets Manager
- Game client has **send-only** SQS permissions
- API Gateway has rate limiting (default)

## 🎯 Game Features

- **10 Progressive Stages** - Increasing difficulty
- **Arrow Key Controls** - ↑ ↓ ← → movement
- **Local-First** - Zero network lag
- **Statistics Tracking** - Moves and time per stage
- **Stage Complete Popups** - Continue to next stage
- **Game Complete Popup** - Different message at end

## 📈 Future Analytics Possibilities

Since all game events go to SQS, you can build:

1. **Analytics Dashboard** - Which levels are hardest?
2. **Leaderboard** - Fastest completion times
3. **Heatmaps** - Common player paths
4. **A/B Testing** - Different maze layouts
5. **Player Retention** - Track return players

Example Lambda consumer for SQS:

```python
# Process SQS messages and write to PostgreSQL
def process_analytics(event):
    for record in event['Records']:
        message = json.loads(record['body'])
        
        if message['event_type'] == 'level_complete':
            # Insert into game_statistics table
            save_to_db(message)
```

## 💰 AWS Costs

**Free Tier Eligible:**
- RDS db.t3.micro: 750 hours/month
- Lambda: 1M requests/month
- SQS: 1M requests/month
- API Gateway: 1M requests/month

**Estimated Monthly Cost (after free tier):**
- RDS: $15-20/month (if always on)
- Lambda: ~$0 (unlikely to exceed free tier)
- SQS: ~$0 (unlikely to exceed free tier)
- **Total: ~$15-20/month**

**Cost Optimization:**
- Stop RDS when not playing
- Use RDS Snapshots for cheaper storage
- Or: Deploy only when playing, destroy when done

## 🧪 Testing the API

```bash
# Test Lambda function directly
aws lambda invoke \
  --function-name maze-game-get-level-data \
  --payload '{"pathParameters":{"stage_number":"1"}}' \
  response.json

cat response.json

# Test via API Gateway
curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/level/1
```

## 🔧 Troubleshooting

### "Failed to connect to API"
- Check `API_GATEWAY_URL` in `.env`
- Verify Lambda is deployed: `terraform output api_gateway_url`
- Test API: `curl $API_GATEWAY_URL/1`

### "Stage not found"
- Database not initialized
- Run `schema.sql` on RDS instance
- Check Lambda logs: `aws logs tail /aws/lambda/maze-game-get-level-data --follow`

### "Analytics not sending"
- Check AWS credentials in `.env`
- Verify SQS URL is correct
- Check IAM permissions for game_client user

### Lambda timeout
- Check VPC configuration
- Ensure subnets have NAT gateway or VPC endpoint for Secrets Manager
- Increase Lambda timeout in `main.tf`

## 🔄 Cleanup

To destroy all AWS resources:

```bash
cd terraform
terraform destroy
```

⚠️ This will delete:
- RDS database (all levels)
- Lambda function
- API Gateway
- SQS queue (all messages)
- All networking resources

## 🎓 Learning Points

This project demonstrates:

1. **Local-First Architecture** - Fast UX with cloud benefits
2. **Serverless Backend** - Lambda + API Gateway
3. **Infrastructure as Code** - Terraform
4. **Async Processing** - SQS for non-critical data
5. **Security Best Practices** - Secrets Manager, VPC, IAM
6. **API Design** - RESTful endpoints
7. **Game Development** - Pygame basics

## 📝 License

Educational project - free to use and modify.
