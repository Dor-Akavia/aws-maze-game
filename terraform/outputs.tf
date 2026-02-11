output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = "${aws_api_gateway_stage.prod.invoke_url}/level"
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.maze_db.endpoint
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.maze_db.db_name
}

output "sqs_queue_url" {
  description = "SQS queue URL for game analytics"
  value       = aws_sqs_queue.game_analytics.url
}

output "sqs_queue_arn" {
  description = "SQS queue ARN"
  value       = aws_sqs_queue.game_analytics.arn
}

output "game_client_access_key_id" {
  description = "IAM Access Key ID for game client"
  value       = aws_iam_access_key.game_client_key.id
  sensitive   = true
}

output "game_client_secret_access_key" {
  description = "IAM Secret Access Key for game client"
  value       = aws_iam_access_key.game_client_key.secret
  sensitive   = true
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.get_level_data.function_name
}

output "web_server_public_ip" {
  description = "Public IP address of web server"
  value       = aws_eip.web_server_eip.public_ip
}

output "web_server_url" {
  description = "URL to access the game"
  value       = "http://${aws_eip.web_server_eip.public_ip}"
}
