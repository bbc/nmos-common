pipeline{
  agent { label 'ipstudio-deps&&16.04' }
  stages {
    stage('Lint') {
      steps {
	flake8
      }
}  
