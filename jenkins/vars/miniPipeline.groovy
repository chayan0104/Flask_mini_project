def call(Map config) {
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

  withAWS(region: 'us-east-1', credentials: 'aws-credentials') {
    sh 'aws ecr get-login-password | docker login --username AWS --password-stdin ' + config.registry

    contexts.each { name, context ->
      def tag = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(7)}"
      sh "docker build -t ${images[name]}:${tag} -t ${images[name]}:latest ${context}"
      sh "docker push ${images[name]}:${tag}"
      sh "docker push ${images[name]}:latest"
    }
  }
}
