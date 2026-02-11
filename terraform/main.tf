terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Lambda Function - Get Level Data
resource "aws_lambda_function" "get_level_data" {
  filename         = "lambda_function.zip"
  function_name    = "maze-game-get-level-data"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  source_code_hash = filebase64sha256("lambda_function.zip")

  # Updated to 3.12 to match the available Klayer
  runtime = "python3.12"
  timeout = 30

  # NEW: Adding the psycopg2-binary layer via ARN
  layers = [
    "arn:aws:lambda:eu-north-1:770693421928:layer:Klayers-p312-psycopg2-binary:2"
  ]

  vpc_config {
    subnet_ids         = [aws_subnet.maze_subnet_1.id, aws_subnet.maze_subnet_2.id]
    security_group_ids = [aws_security_group.lambda_sg.id]
  }

  environment {
    variables = {
      SECRET_ARN = aws_secretsmanager_secret.db_credentials.arn
    }
  }

  tags = {
    Name = "maze-game-get-level-data"
  }
}
