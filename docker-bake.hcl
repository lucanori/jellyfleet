target "docker-metadata-action" {}

variable "APP" {
  default = "jellyfleet"
}

variable "VERSION" {
  default = "latest"
}

variable "NODE_VERSION" {
  default = "22"
}

variable "SOURCE" {
  default = "https://github.com/lucanori/jellyfleet"
}

group "default" {
  targets = ["image-local"]
}

target "image" {
  inherits = ["docker-metadata-action"]
  dockerfile = "Dockerfile"
  context = "."
  args = {
    NODE_VERSION = "${NODE_VERSION}"
    BUILD_ENV = "production"
  }
  labels = {
    "org.opencontainers.image.source" = "${SOURCE}"
    "org.opencontainers.image.title" = "jellyfleet"
    "org.opencontainers.image.description" = "sync all your jellyfin instances"
  }
  cache-from = [
    "type=gha"
  ]
  cache-to = [
    "type=gha,mode=max"
  ]
}

target "image-local" {
  inherits = ["image"]
  output = ["type=docker"]
  tags = ["${APP}:${VERSION}"]
}

target "image-all" {
  inherits = ["image"]
  platforms = [
    "linux/amd64",
    "linux/arm64"
  ]
  output = ["type=registry"]
}

target "test" {
  inherits = ["image"]
  target = "test"
  output = ["type=cacheonly"]
  cache-from = [
    "type=gha,scope=test"
  ]
  cache-to = [
    "type=gha,mode=max,scope=test"
  ]
} 