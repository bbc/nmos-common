@Library("rd-apmm-groovy-ci-library@master") _

pipeline{
  agent { label 'ipstudio-deps&&16.04' }
  environment {
    http_proxy = "http://www-cache.rd.bbc.co.uk:8080"
    https_proxy = "http://www-cache.rd.bbc.co.uk:8080"
  }
  stages {
    stage('Test') {
      steps{
        withBBCRDPythonArtifactory {
          sh 'tox --recreate --workdir /tmp/$(basename ${WORKSPACE})'
        }
      }
    }
    stage('Lint') {
      steps {
	      sh 'flake8'
      }
    }
  }
}
