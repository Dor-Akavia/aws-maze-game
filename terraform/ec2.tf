# EC2 Security Group
resource "aws_security_group" "web_server_sg" {
  name        = "maze-game-web-server-sg"
  description = "Security group for web server"
  vpc_id      = aws_vpc.maze_vpc.id

  # HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP from anywhere"
  }

  # HTTPS (for future)
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTPS from anywhere"
  }

  # SSH (restrict to your IP in production)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Change to your IP for security
    description = "Allow SSH"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "maze-game-web-server-sg"
  }
}

# EC2 Instance
resource "aws_instance" "web_server" {
  ami           = var.ec2_ami_id # Ubuntu 24.04 LTS
  instance_type = var.ec2_instance_type
  key_name      = var.ec2_key_name

  subnet_id                   = aws_subnet.maze_subnet_1.id
  vpc_security_group_ids      = [aws_security_group.web_server_sg.id]
  associate_public_ip_address = true

  user_data = templatefile("${path.module}/user_data.sh", {
    api_gateway_url = aws_api_gateway_stage.prod.invoke_url
    sqs_queue_url   = aws_sqs_queue.game_analytics.url
  })

  tags = {
    Name = "maze-game-web-server"
  }
}

# Elastic IP for web server
resource "aws_eip" "web_server_eip" {
  instance = aws_instance.web_server.id
  domain   = "vpc"

  tags = {
    Name = "maze-game-web-server-eip"
  }

  depends_on = [aws_internet_gateway.maze_igw]
}
