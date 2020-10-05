pipeline {
  agent none
  stages {
    stage('Static Analysis') {
      parallel {
        stage('python3') {
          agent {
            dockerfile {
              // Large image with full OpenModelica build dependencies; lacks omc and OMPython
              label 'linux'
              dir '.jenkins/python3'
              additionalBuildArgs '--pull'
            }
          }
          steps {
            sh 'pylint *'
          }
        }
      }
    }
  }
}
