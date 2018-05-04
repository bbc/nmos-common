pipeline{
  agent { label 'ipstudio-deps&&16.04' }
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
