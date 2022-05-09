pipeline {
  agent none
  stages {
    stage('test') {
      parallel {
        stage('python3') {
          agent {
            dockerfile {
              label 'linux'
              dir '.jenkins/python3'
              additionalBuildArgs '--pull'
            }
          }
          steps {
            sh 'hostname'
            sh 'HOME="$PWD" python3 setup.py install --user'
            sh '''
            export HOME="$PWD"
            pytest -v --junit-xml=py3.xml tests
            '''
            junit 'py3.xml'
          }
        }
      }
    }
  }
}
