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
            testsResultsDir="$PWD/testsResults"
            mkdir testsResultsDir
            ORIGINAL_TEMP=$TEMP
            ORIGINAL_TMP=$TMP
            ORIGINAL_TMPDIR=$TMPDIR
            export TEMP=$testsResultsDir
            export TMP=$testsResultsDir
            export TMPDIR=$testsResultsDir
            pytest -v --junit-xml=py3.xml tests
            export TEMP=$ORIGINAL_TEMP
            export TMP=$ORIGINAL_TMP
            export TMPDIR=$ORIGINAL_TMPDIR
            rm -rf $testsResultsDir
            '''
            junit 'py3.xml'
          }
        }
      }
    }
  }
}
