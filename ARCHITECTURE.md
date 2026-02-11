# Architecture Documentation

## Overview: Local-First with Cloud Backend

This architecture demonstrates a modern approach to game development where:
- **Performance-critical operations** run locally (movement, collision)
- **Data storage and analytics** use cloud services asynchronously
- **Network requests** only happen when necessary (level loading)

## Why Local-First?

### Problems with "Cloud-First" Approach

If we sent every movement through SQS:
```
Player presses ↑
  ↓
Send to SQS (100ms)
  ↓
Lambda processes (50ms)
  ↓
Update position in DB (50ms)
  ↓
Send response back (100ms)
  ↓
Player moves (300ms total) ❌
```

**Result**: Laggy, unplayable game

### Solution: Local-First

```
Player presses ↑
  ↓
Check collision locally (0ms)
  ↓
Update position locally (0ms)
  ↓
Render immediately (16ms)
  ↓
Player moves (16ms total) ✅
```

**Result**: Instant, smooth gameplay

## Component Responsibilities

### 1. Python Game Client (Local)

**Responsibilities:**
- Render game graphics
- Handle user input
- Calculate player movement
- Detect collisions with walls
- Track statistics (moves, time)

**Does NOT:**
- Store level data permanently
- Wait for network confirmations
- Query database directly

**Technology:** Pygame (Python game library)

### 2. API Gateway + Lambda (Cloud)

**Responsibilities:**
- Provide level data on request
- Act as secure gateway to database
- Handle authentication/authorization (future)
- Rate limiting

**Does NOT:**
- Process player movements
- Handle real-time gameplay
- Store game state

**Technology:** AWS Lambda (Python), API Gateway

**API Endpoint:**
```
GET /level/{stage_number}

Response:
{
  "success": true,
  "data": {
    "stage_number": 1,
    "layout": "###########\n#S........#\n...",
    "width": 11,
    "height": 9,
    "start_x": 1,
    "start_y": 1,
    "end_x": 9,
    "end_y": 7
  }
}
```

### 3. PostgreSQL RDS (Cloud)

**Responsibilities:**
- Store all 10 maze stages
- Persist game analytics (future)
- Source of truth for level data

**Does NOT:**
- Receive direct connections from game client
- Handle real-time queries
- Track live player positions

**Tables:**
- `maze_stages` - Level layouts
- `game_statistics` - Analytics data (populated by SQS consumer)

### 4. SQS Queue (Cloud)

**Responsibilities:**
- Receive game events asynchronously
- Buffer analytics data
- Decouple game from analytics processing

**Does NOT:**
- Process events immediately
- Affect gameplay
- Provide responses to game client

**Message Types:**
- `game_start` - Player started playing
- `level_complete` - Player finished a stage
- `game_complete` - Player finished all stages

### 5. Secrets Manager (Cloud)

**Responsibilities:**
- Store database credentials securely
- Provide credentials to Lambda
- Rotate secrets (optional)

**Does NOT:**
- Expose credentials to game client
- Store API keys for game

## Data Flow

### Scenario 1: Game Start

```
┌─────────┐
│  Game   │
└────┬────┘
     │
     │ 1. GET /level/1
     ↓
┌─────────────┐
│ API Gateway │
└─────┬───────┘
      │
      │ 2. Invoke Lambda
      ↓
┌─────────────┐       ┌──────────────────┐
│   Lambda    │──3──► │ Secrets Manager  │
│             │◄──4── │ (Get DB creds)   │
└─────┬───────┘       └──────────────────┘
      │
      │ 5. Query stage 1
      ↓
┌─────────────┐
│ PostgreSQL  │
└─────┬───────┘
      │
      │ 6. Return layout
      ↓
┌─────────────┐
│   Lambda    │
└─────┬───────┘
      │
      │ 7. JSON response
      ↓
┌─────────────┐
│  API GW     │
└─────┬───────┘
      │
      │ 8. Level data
      ↓
┌─────────┐
│  Game   │ ──► Parse & render locally
└─────────┘
```

### Scenario 2: Player Movement (100% Local)

```
Player presses ↑
     │
     ↓
┌─────────────────────┐
│  Game (Local)       │
│                     │
│  if maze[y-1][x] != '#':
│      y = y - 1      │ ◄── No network calls!
│      render()       │
└─────────────────────┘
     │
     ↓
Screen updates instantly
```

### Scenario 3: Level Complete

```
Player reaches exit
     │
     ↓
┌─────────────────────┐
│  Game (Local)       │
│                     │
│  • Calculate time   │
│  • Count moves      │
│  • Show popup       │
└─────┬───────────────┘
      │
      │ Fire & forget
      │ (async, non-blocking)
      ↓
┌─────────────────────┐
│    SQS Queue        │
│                     │
│  Message:           │
│  {                  │
│    "event": "level_complete",
│    "stage": 1,      │
│    "time": 45.3,    │
│    "moves": 78      │
│  }                  │
└─────────────────────┘
      │
      │ Later...
      │ (processed by analytics worker)
      ↓
┌─────────────────────┐
│   PostgreSQL        │
│   (game_statistics) │
└─────────────────────┘
```

## Security Architecture

### Network Isolation

```
┌─────────────────────────────────────────────┐
│             Public Internet                  │
└───┬────────────────────────────────────┬────┘
    │                                    │
    │ HTTPS                              │ HTTPS
    ↓                                    ↓
┌─────────────┐                    ┌─────────────┐
│ API Gateway │                    │ Game Client │
│ (Public)    │                    │ (Local)     │
└─────┬───────┘                    └─────┬───────┘
      │                                  │
      │ Invoke                           │ Send messages
      ↓                                  ↓
┌─────────────┐                    ┌─────────────┐
│   Lambda    │                    │  SQS Queue  │
│   (VPC)     │                    │  (Public)   │
└─────┬───────┘                    └─────────────┘
      │
      │ Private subnet
      ↓
┌─────────────┐
│ PostgreSQL  │
│ (Private)   │◄──── NOT accessible from internet
└─────────────┘
```

### IAM Permissions

**Lambda Role:**
- ✅ Read from Secrets Manager
- ✅ Connect to RDS (via VPC)
- ✅ Write CloudWatch logs

**Game Client Credentials:**
- ✅ Send messages to SQS
- ❌ Receive messages from SQS
- ❌ Access RDS
- ❌ Invoke Lambda directly

### Secrets Management

- Database password **NEVER** in code
- Stored in AWS Secrets Manager
- Only Lambda can access
- Can rotate without code changes

## Scalability

### Current Architecture (1-100 players)

```
API Gateway → Lambda → RDS
    ↓
 Scales automatically
 (up to Lambda concurrency limit)
```

### Future: High Traffic (1000+ players)

```
API Gateway → Lambda → ElastiCache (Redis)
                            ↓
                     (Cache level data)
                            ↓
                     Only on cache miss → RDS
```

**Benefits:**
- Reduce RDS load
- Faster response times
- Lower costs

## Cost Analysis

### Per-Player Cost (Monthly)

**Assumptions:**
- 100 players
- Each plays 3 times/month
- Average 20 minutes per session
- All 10 stages completed

**Calculations:**

| Service | Usage | Cost |
|---------|-------|------|
| API Gateway | 100 players × 3 sessions × 10 levels = 3,000 requests | $0.01 |
| Lambda | 3,000 invocations × 100ms avg = 300 seconds | $0.00 |
| SQS | 3,000 messages | $0.00 |
| RDS | 720 hours (always on) | $15.00 |
| Data Transfer | ~1MB total | $0.00 |
| **TOTAL** | | **$15.01** |

**Optimization:**
- Stop RDS when not in use → **~$5/month**
- Use RDS snapshots → **~$1/month storage**

### Break-Even Analysis

When does cloud make sense vs local SQLite?

**Cloud Benefits:**
- Multiplayer support
- Centralized analytics
- No database management
- Scalable infrastructure

**Worth it if:**
- 10+ concurrent players
- Need analytics
- Want to avoid server management
- Rapid iteration on levels

## Monitoring

### Key Metrics

**Game Performance:**
- Average time per stage
- Move count per stage
- Completion rate

**API Health:**
- API Gateway 4xx/5xx errors
- Lambda duration
- Lambda errors

**Infrastructure:**
- RDS CPU/Memory
- SQS queue depth
- Lambda concurrency

### Alerts

```yaml
# CloudWatch Alarms (future)

API_Latency_High:
  Threshold: > 500ms
  Action: SNS notification

Lambda_Error_Rate:
  Threshold: > 5%
  Action: SNS notification

RDS_CPU_High:
  Threshold: > 80%
  Action: SNS notification

SQS_Queue_Depth:
  Threshold: > 1000 messages
  Action: SNS notification
```

## Future Enhancements

### 1. Multiplayer Support

Add WebSocket API for real-time player positions:

```
┌─────────┐
│ Player  │
└────┬────┘
     │
     │ WebSocket
     ↓
┌─────────────┐
│  API GW     │
│ (WebSocket) │
└─────┬───────┘
      │
      ↓
┌─────────────┐
│  Lambda     │
└─────┬───────┘
      │
      ↓
┌─────────────┐
│ DynamoDB    │ ◄── Store live positions
└─────────────┘
```

### 2. Leaderboard

Process SQS messages and create rankings:

```
SQS → Lambda → DynamoDB (leaderboard)
                   ↓
              API → Game (show top 10)
```

### 3. User Accounts

Add authentication:

```
Game → Cognito → API Gateway (with authorizer)
```

### 4. Custom Levels

Let players create and share:

```
Game → API (POST /level) → S3 (storage)
                          → DynamoDB (metadata)
```

## Conclusion

This architecture demonstrates:

1. **Local-First** for performance-critical operations
2. **Cloud Backend** for data persistence and analytics  
3. **Async Processing** for non-blocking operations
4. **Security Best Practices** with IAM and Secrets Manager
5. **Cost Efficiency** with serverless architecture
6. **Scalability** with managed services

Perfect for games that need cloud features without sacrificing performance!
