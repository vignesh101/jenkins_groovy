pipeline {
    agent any

    parameters {
        string(name: 'FOLDER_NAME', defaultValue: '', description: 'Name of the folder to create Sybase jobs and credentials in')
        string(name: 'NUM_JOBS', defaultValue: '10', description: 'Number of Sybase jobs and credentials to create')
    }

    environment {
        SCRIPT_PATH = 'create_jobs_with_credentials.py'
        JENKINS_URL = 'http://localhost:8080'
        JENKINS_CREDS = credentials('jenkins_id')
    }

    stages {
        stage('Validate Input') {
            steps {
                script {
                    if (params.FOLDER_NAME == '') {
                        error "FOLDER_NAME parameter is required. Please provide a folder name."
                    }
                    if (!params.NUM_JOBS.isInteger() || params.NUM_JOBS.toInteger() <= 0) {
                        error "NUM_JOBS must be a positive integer."
                    }
                }
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh '''
                python3 -m venv venv
                . venv/bin/activate
                pip install requests
                '''
            }
        }

        stage('Execute Python Script') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'jenkins_id', usernameVariable: 'JENKINS_USER', passwordVariable: 'JENKINS_API_TOKEN')]) {
                        sh '''
                        . venv/bin/activate
                        python3 ${SCRIPT_PATH} "${JENKINS_URL}" "${JENKINS_USER}" "${JENKINS_API_TOKEN}" "${FOLDER_NAME}" "${NUM_JOBS}"
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}