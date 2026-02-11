# Security Group for RDS
resource "aws_security_group" "rds_sg" {
  name        = "maze-game-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = aws_vpc.maze_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda_sg.id]
    description     = "Allow Lambda to access RDS"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "maze-game-rds-sg"
  }
}

# Security Group for Lambda
resource "aws_security_group" "lambda_sg" {
  name        = "maze-game-lambda-sg"
  description = "Security group for Lambda functions"
  vpc_id      = aws_vpc.maze_vpc.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "maze-game-lambda-sg"
  }
}

# RDS Subnet Group
resource "aws_db_subnet_group" "maze_db_subnet_group" {
  name       = "maze-game-db-subnet-group"
  subnet_ids = [aws_subnet.maze_subnet_1.id, aws_subnet.maze_subnet_2.id]

  tags = {
    Name = "maze-game-db-subnet-group"
  }
}

