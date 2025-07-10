variable "ingestion_docker_image_tag" {
  type        = string
  description = "Docker image tag for the ingestion lambda"
}

variable "silver_docker_image_tag" {
  type        = string
  description = "Docker image tag for the silver transform lambda"
}

variable "gold_docker_image_tag" {
  type        = string
  description = "Docker image tag for the gold transform lambda"
}
