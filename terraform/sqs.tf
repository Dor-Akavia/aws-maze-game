# SQS Queue for Game Analytics (Level Complete Events)
resource "aws_sqs_queue" "game_analytics" {
  name                      = "maze-game-analytics"
  delay_seconds             = 0
  max_message_size          = 2048
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10

  tags = {
    Name = "maze-game-analytics"
  }
}

# IAM User for Game Client (to send SQS messages)
resource "aws_iam_user" "game_client" {
  name = "maze-game-client"

  tags = {
    Name = "maze-game-client"
  }
}

resource "aws_iam_access_key" "game_client_key" {
  user = aws_iam_user.game_client.name
}

# IAM Policy for Game Client - SQS Send Only
resource "aws_iam_user_policy" "game_client_sqs_policy" {
  name = "maze-game-client-sqs-policy"
  user = aws_iam_user.game_client.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueUrl"
        ]
        Resource = aws_sqs_queue.game_analytics.arn
      }
    ]
  })
}