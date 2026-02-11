# Quick Start Guide

## 🚀 5-Minute Setup

### 1. Build Lambda Package
```bash
cd lambda
./build.sh
```

### 2. Deploy Infrastructure
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Set db_password

terraform init
terraform apply -auto-approve
```

### 3. Save Outputs
```bash
terraform output -json > outputs.json

# Extract key values
export API_URL=$(terraform output -raw api_gateway_url)
export SQS_URL=$(terraform output -raw sqs_queue_url)
export AWS_KEY=$(terraform output -raw game_client_access_key_id)
export AWS_SECRET=$(terraform output -raw game_client_secret_access_key)
export RDS_ENDPOINT=$(terraform output -raw rds_endpoint)

echo "API Gateway: $API_URL"
echo "SQS Queue: $SQS_URL"
```

### 4. Initialize Database
```bash
cd ../database

# Temporarily allow your IP to RDS
# Go to AWS Console → RDS → maze-game-db → Security Group
# Add inbound rule: PostgreSQL (5432) from YOUR_IP

# Run schema
psql -h $RDS_ENDPOINT -U mazegameadmin -d mazegame -f schema.sql

# Password: (from terraform.tfvars)

# REMOVE the temporary security group rule!
```

### 5. Configure Game
```bash
cd ../app

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env
cat > .env << EOF
API_GATEWAY_URL=$API_URL
AWS_REGION=us-east-1
SQS_QUEUE_URL=$SQS_URL
AWS_ACCESS_KEY_ID=$AWS_KEY
AWS_SECRET_ACCESS_KEY=$AWS_SECRET
PLAYER_ID=$(whoami)
EOF
```

### 6. Play!
```bash
python maze_game.py
```

## 🎮 Controls

- **↑** - Move up
- **↓** - Move down
- **←** - Move left
- **→** - Move right

## 🧹 Cleanup

```bash
cd terraform
terraform destroy -auto-approve
```

## 🔍 Verify Setup

### Test API
```bash
curl $API_URL/1 | jq
```

Expected response:
```json
{
  "success": true,
  "data": {
    "stage_number": 1,
    "layout": "###########\n#S........#\n...",
    "width": 11,
    "height": 9,
    ...
  }
}
```

### Test Lambda
```bash
aws lambda invoke \
  --function-name maze-game-get-level-data \
  --payload '{"pathParameters":{"stage_number":"1"}}' \
  response.json

cat response.json | jq
```

### Check SQS Messages (after playing)
```bash
aws sqs receive-message \
  --queue-url $SQS_URL \
  --max-number-of-messages 10 | jq
```

## 🐛 Common Issues

**"ModuleNotFoundError: No module named 'pygame'"**
```bash
pip install -r requirements.txt
```

**"Failed to connect to API"**
- Check API_GATEWAY_URL in .env
- Test: `curl $API_URL/1`

**"Stage not found"**
- Database not initialized
- Run schema.sql

**"Lambda timeout"**
- Check Lambda VPC configuration
- Increase timeout in main.tf

## 📊 Monitor

### Lambda Logs
```bash
aws logs tail /aws/lambda/maze-game-get-level-data --follow
```

### SQS Queue Depth
```bash
aws sqs get-queue-attributes \
  --queue-url $SQS_URL \
  --attribute-names ApproximateNumberOfMessages
```

### RDS Status
```bash
aws rds describe-db-instances \
  --db-instance-identifier maze-game-db \
  --query 'DBInstances[0].DBInstanceStatus'
```
