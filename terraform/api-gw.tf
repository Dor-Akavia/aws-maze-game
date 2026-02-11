# API Gateway REST API
resource "aws_api_gateway_rest_api" "maze_api" {
  name        = "maze-game-api"
  description = "API for Maze Game"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name = "maze-game-api"
  }
}

# API Gateway Resource - /level
resource "aws_api_gateway_resource" "level_resource" {
  rest_api_id = aws_api_gateway_rest_api.maze_api.id
  parent_id   = aws_api_gateway_rest_api.maze_api.root_resource_id
  path_part   = "level"
}

# API Gateway Resource - /level/{stage_number}
resource "aws_api_gateway_resource" "level_stage_resource" {
  rest_api_id = aws_api_gateway_rest_api.maze_api.id
  parent_id   = aws_api_gateway_resource.level_resource.id
  path_part   = "{stage_number}"
}

# API Gateway Method - GET /level/{stage_number}
resource "aws_api_gateway_method" "get_level" {
  rest_api_id   = aws_api_gateway_rest_api.maze_api.id
  resource_id   = aws_api_gateway_resource.level_stage_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

# API Gateway Integration with Lambda
resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.maze_api.id
  resource_id             = aws_api_gateway_resource.level_stage_resource.id
  http_method             = aws_api_gateway_method.get_level.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_level_data.invoke_arn
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_level_data.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.maze_api.execution_arn}/*/${aws_api_gateway_method.get_level.http_method}${aws_api_gateway_resource.level_stage_resource.path}"
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "maze_api_deployment" {
  depends_on = [
    aws_api_gateway_integration.lambda_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.maze_api.id

  lifecycle {
    create_before_destroy = true
  }

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.level_resource.id,
      aws_api_gateway_resource.level_stage_resource.id,
      aws_api_gateway_method.get_level.id,
      aws_api_gateway_integration.lambda_integration.id,
    ]))
  }
}

# API Gateway Stage
resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.maze_api_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.maze_api.id
  stage_name    = "prod"

  tags = {
    Name = "maze-game-api-prod"
  }
}

# Enable CORS for API Gateway
resource "aws_api_gateway_method" "options_method" {
  rest_api_id   = aws_api_gateway_rest_api.maze_api.id
  resource_id   = aws_api_gateway_resource.level_stage_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_integration" {
  rest_api_id = aws_api_gateway_rest_api.maze_api.id
  resource_id = aws_api_gateway_resource.level_stage_resource.id
  http_method = aws_api_gateway_method.options_method.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_200" {
  rest_api_id = aws_api_gateway_rest_api.maze_api.id
  resource_id = aws_api_gateway_resource.level_stage_resource.id
  http_method = aws_api_gateway_method.options_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.maze_api.id
  resource_id = aws_api_gateway_resource.level_stage_resource.id
  http_method = aws_api_gateway_method.options_method.http_method
  status_code = aws_api_gateway_method_response.options_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  depends_on = [aws_api_gateway_integration.options_integration]
}