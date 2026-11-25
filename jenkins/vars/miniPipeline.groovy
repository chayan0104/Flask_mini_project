def call(Map config) {
  if (!(config.environment in ['dev', 'uat'])) {
    error("Unsupported deployment environment: ${config.environment}")
  }

  def images = [
    frontend: "${config.registry}/mini-platform/frontend",
    users: "${config.registry}/mini-platform/users",
    orders: "${config.registry}/mini-platform/orders"
  ]
  def contexts = [
    frontend: config.frontendContext,
    users: config.usersContext,
    orders: config.ordersContext
  ]

  withAWS(region: config.region, credentials: 'aws-credentials') {
    sh 'aws ecr get-login-password | docker login --username AWS --password-stdin ' + config.registry

    contexts.each { name, context ->
      def buildTag = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(7)}"
      def environmentTag = config.environment
      sh "docker build -t ${images[name]}:${buildTag} -t ${images[name]}:${environmentTag} -t ${images[name]}:latest ${context}"
      sh "docker push ${images[name]}:${buildTag}"
      sh "docker push ${images[name]}:${environmentTag}"
      sh "docker push ${images[name]}:latest"
    }
  }
}
