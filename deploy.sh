#!/bin/bash

# Maze Game Deployment Script
# This script helps automate the deployment process

set -e

echo "====================================="
echo "Maze Game Deployment Helper"
echo "====================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}Error: Terraform is not installed${NC}"
        echo "Install from: https://www.terraform.io/downloads"
        exit 1
    fi
    echo -e "${GREEN}✓ Terraform found${NC}"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}Error: AWS CLI is not installed${NC}"
        echo "Install from: https://aws.amazon.com/cli/"
        exit 1
    fi
    echo -e "${GREEN}✓ AWS CLI found${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python 3 found${NC}"
    
    # Check psql
    if ! command -v psql &> /dev/null; then
        echo -e "${YELLOW}Warning: psql is not installed${NC}"
        echo "You'll need it to initialize the database"
    else
        echo -e "${GREEN}✓ psql found${NC}"
    fi
    
    echo ""
}

# Deploy infrastructure
deploy_infrastructure() {
    echo "====================================="
    echo "Step 1: Deploy Infrastructure"
    echo "====================================="
    
    cd terraform
    
    if [ ! -f "terraform.tfvars" ]; then
        echo -e "${YELLOW}terraform.tfvars not found. Creating from example...${NC}"
        cp terraform.tfvars.example terraform.tfvars
        echo -e "${RED}Please edit terraform/terraform.tfvars with your values${NC}"
        echo "Then run this script again"
        exit 1
    fi
    
    echo "Initializing Terraform..."
    terraform init
    
    echo ""
    echo "Planning deployment..."
    terraform plan
    
    echo ""
    read -p "Deploy infrastructure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Deployment cancelled"
        exit 0
    fi
    
    echo "Deploying..."
    terraform apply -auto-approve
    
    echo ""
    echo -e "${GREEN}Infrastructure deployed successfully!${NC}"
    echo ""
    echo "Saving outputs..."
    terraform output -json > ../outputs.json
    
    cd ..
}

# Setup database
setup_database() {
    echo "====================================="
    echo "Step 2: Initialize Database"
    echo "====================================="
    
    if [ ! -f "outputs.json" ]; then
        echo -e "${RED}Error: outputs.json not found${NC}"
        echo "Run deployment first"
        exit 1
    fi
    
    DB_ENDPOINT=$(cat outputs.json | grep -o '"rds_endpoint"[^}]*' | grep -o '"value"[^"]*' | sed 's/"value": "//g' | tr -d '"')
    DB_NAME=$(cat outputs.json | grep -o '"rds_database_name"[^}]*' | grep -o '"value"[^"]*' | sed 's/"value": "//g' | tr -d '"')
    
    echo "Database endpoint: $DB_ENDPOINT"
    echo "Database name: $DB_NAME"
    echo ""
    
    read -p "Initialize database with schema? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Skipping database initialization"
        return
    fi
    
    read -p "Database username (default: mazegameadmin): " DB_USER
    DB_USER=${DB_USER:-mazegameadmin}
    
    echo "Connecting to database..."
    PGPASSWORD=$(grep db_password terraform/terraform.tfvars | cut -d '=' -f 2 | tr -d ' "')
    
    psql -h "$DB_ENDPOINT" -U "$DB_USER" -d "$DB_NAME" -f database/schema.sql
    
    echo -e "${GREEN}Database initialized successfully!${NC}"
}

# Setup Python environment
setup_python() {
    echo "====================================="
    echo "Step 3: Setup Python Environment"
    echo "====================================="
    
    cd app
    
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    echo "Activating virtual environment..."
    source venv/bin/activate
    
    echo "Installing dependencies..."
    pip install -r requirements.txt
    
    if [ ! -f ".env" ]; then
        echo "Creating .env file from outputs..."
        cp .env.example .env
        
        # Extract values from Terraform outputs
        if [ -f "../outputs.json" ]; then
            DB_ENDPOINT=$(cat ../outputs.json | grep -o '"rds_endpoint"[^}]*' | grep -o '"value"[^"]*' | sed 's/"value": "//g' | tr -d '"')
            SQS_URL=$(cat ../outputs.json | grep -o '"sqs_queue_url"[^}]*' | grep -o '"value"[^"]*' | sed 's/"value": "//g' | tr -d '"')
            
            sed -i.bak "s|DB_HOST=.*|DB_HOST=$DB_ENDPOINT|g" .env
            sed -i.bak "s|SQS_QUEUE_URL=.*|SQS_QUEUE_URL=$SQS_URL|g" .env
            rm .env.bak
            
            echo -e "${YELLOW}Please edit app/.env to add:${NC}"
            echo "  - DB_PASSWORD"
            echo "  - AWS_ACCESS_KEY_ID"
            echo "  - AWS_SECRET_ACCESS_KEY"
        fi
    fi
    
    echo -e "${GREEN}Python environment setup complete!${NC}"
    cd ..
}

# Main menu
main() {
    check_prerequisites
    
    echo "What would you like to do?"
    echo "1. Full deployment (all steps)"
    echo "2. Deploy infrastructure only"
    echo "3. Setup database only"
    echo "4. Setup Python environment only"
    echo "5. Exit"
    echo ""
    read -p "Choose an option (1-5): " choice
    
    case $choice in
        1)
            deploy_infrastructure
            setup_database
            setup_python
            echo ""
            echo -e "${GREEN}✓ Full deployment complete!${NC}"
            echo ""
            echo "Next steps:"
            echo "1. Edit app/.env with remaining credentials"
            echo "2. Run the game: cd app && source venv/bin/activate && python maze_game.py"
            ;;
        2)
            deploy_infrastructure
            ;;
        3)
            setup_database
            ;;
        4)
            setup_python
            ;;
        5)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid option"
            exit 1
            ;;
    esac
}

main
