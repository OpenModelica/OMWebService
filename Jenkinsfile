pipeline {
  agent none
  stages {
    stage('test') {
      parallel {
        stage('python3') {
          agent {
            label 'linux'
          }
          steps {
            script {
              def deps = docker.build('omwebservice-jenkins-python3', '--pull .jenkins/python3')
              def dockergid = sh (script: 'stat -c %g /var/run/docker.sock', returnStdout: true).trim()
              sh "docker pull openmodelica/openmodelica:v1.18.0-minimal" // Avoid timeout
              deps.inside("-v /var/run/docker.sock:/var/run/docker.sock --network=host --pid=host --group-add '${dockergid}'") {
                sh 'python3 setup.py build'
                timeout(3) {
                  sh label: 'RunTests', script: '''
                  testsResultsDir="$PWD/testsResults"
                  ORIGINAL_TEMP=$TEMP
                  ORIGINAL_TMP=$TMP
                  ORIGINAL_TMPDIR=$TMPDIR
                  export TEMP=$testsResultsDir
                  export TMP=$testsResultsDir
                  export TMPDIR=$testsResultsDir
                  python3 /usr/local/bin/py.test -v --junitxml py3.xml tests
                  export TEMP=$ORIGINAL_TEMP
                  export TMP=$ORIGINAL_TMP
                  export TMPDIR=$ORIGINAL_TMPDIR
                  rm -rf $testsResultsDir
                  '''
                }
                sh 'HOME="$PWD" python3 setup.py install --user'
              }
              junit 'py3.xml'
            }
          }
        }
      }
    }
  }
}
