# Secrets Manager for DB credentials
resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "maze-game/db-credentials"
  description             = "Database credentials for Maze Game"
  recovery_window_in_days = 0 # Set to 0 for immediate deletion (dev only)

  tags = {
    Name = "maze-game-db-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    host     = aws_db_instance.maze_db.endpoint
    port     = 5432
    database = aws_db_instance.maze_db.db_name
    username = var.db_username
    password = var.db_password
  })
}
