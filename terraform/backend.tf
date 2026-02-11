terraform {
  backend "s3" {
    bucket         = "maze-game-tf-state"
    key            = "dev/terraform.tfstate"
    region         = "eu-north-1"
    encrypt        = true
    dynamodb_table = "maze-game-tf-lock" # Optional but recommended for locking
  }
}