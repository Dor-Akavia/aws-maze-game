# VPC Configuration
resource "aws_vpc" "maze_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "maze-game-vpc"
  }
}

resource "aws_subnet" "maze_subnet_1" {
  vpc_id            = aws_vpc.maze_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name = "maze-game-subnet-1"
  }
}

resource "aws_subnet" "maze_subnet_2" {
  vpc_id            = aws_vpc.maze_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"

  tags = {
    Name = "maze-game-subnet-2"
  }
}

resource "aws_internet_gateway" "maze_igw" {
  vpc_id = aws_vpc.maze_vpc.id

  tags = {
    Name = "maze-game-igw"
  }
}

resource "aws_route_table" "maze_route_table" {
  vpc_id = aws_vpc.maze_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.maze_igw.id
  }

  tags = {
    Name = "maze-game-route-table"
  }
}


# VPC Endpoint for Secrets Manager (so Lambda can access it without internet)
resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = aws_vpc.maze_vpc.id
  service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.maze_subnet_1.id, aws_subnet.maze_subnet_2.id]
  security_group_ids  = [aws_security_group.vpc_endpoint_sg.id]
  private_dns_enabled = true

  tags = {
    Name = "maze-game-secretsmanager-endpoint"
  }
}

# Security Group for VPC Endpoints
resource "aws_security_group" "vpc_endpoint_sg" {
  name        = "maze-game-vpc-endpoint-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = aws_vpc.maze_vpc.id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda_sg.id]
    description     = "Allow Lambda to access VPC endpoints"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "maze-game-vpc-endpoint-sg"
  }
}

resource "aws_route_table_association" "subnet_1_association" {
  subnet_id      = aws_subnet.maze_subnet_1.id
  route_table_id = aws_route_table.maze_route_table.id
}

resource "aws_route_table_association" "subnet_2_association" {
  subnet_id      = aws_subnet.maze_subnet_2.id
  route_table_id = aws_route_table.maze_route_table.id
}
