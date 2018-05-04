pipeline{
  agent { label 'ipstudio-deps&&16.04' }
  stages {
    stage('Lint') {
      steps {
	sh 'flake8'
      }
    }
    stage('Test') {
      steps{
        sh 'make test'
      }
    }
  }
}
