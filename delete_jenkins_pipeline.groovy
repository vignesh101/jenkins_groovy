pipeline {
    agent any

    parameters {
        string(name: 'FOLDER_NAME', defaultValue: '', description: 'Name of the folder containing Sybase credentials to delete')
    }

    environment {
        SCRIPT_PATH = 'delete_folder_domain_credentials.py'
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

        stage('Execute Groovy Script') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'jenkins_id', usernameVariable: 'JENKINS_USER', passwordVariable: 'JENKINS_API_TOKEN')]) {
                        sh '''
                        . venv/bin/activate
                        python3 ${SCRIPT_PATH} "${JENKINS_URL}" "${JENKINS_USER}" "${JENKINS_API_TOKEN}"
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
