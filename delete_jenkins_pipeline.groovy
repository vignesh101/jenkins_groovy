pipeline {
    agent any

    parameters {
        string(name: 'FOLDER_NAME', defaultValue: '', description: 'Name of the folder containing Sybase credentials to delete')
    }

    environment {
        SCRIPT_PATH = 'delete_folder_domain_credentials.groovy'
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

        stage('Execute Groovy Script') {
            steps {
                script {
                    def scriptContent = readFile(env.SCRIPT_PATH)
                    def result = Jenkins.instance.scriptler.runScript(scriptContent, [params.FOLDER_NAME])
                    echo "Script execution result: ${result}"
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
