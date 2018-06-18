pipeline{
  agent { label 'ipstudio-deps&&16.04' }
  environment {
    http_proxy = "http://www-cache.rd.bbc.co.uk:8080"
    https_proxy = "http://www-cache.rd.bbc.co.uk:8080"
  }
  stages {
    stage('Test') {
      steps{
        sh 'make test'
      }
    }
    stage('Lint') {
      steps {
	      sh 'flake8'
      }
    }
  }
}
