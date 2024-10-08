import argparse
import requests
from requests.auth import HTTPBasicAuth


def parse_arguments():
    parser = argparse.ArgumentParser(description='Create Sybase jobs and credentials in Jenkins folder.')
    parser.add_argument('jenkins_url', help='Jenkins URL')
    parser.add_argument('username', help='Jenkins username')
    parser.add_argument('password', help='Jenkins password or API token')
    parser.add_argument('folder', help='Folder name')
    parser.add_argument('num_jobs', type=int, help='Number of jobs and credentials to create')
    return parser.parse_args()


def execute_groovy_script(jenkins_url, username, password, script):
    url = f"{jenkins_url}/scriptText"
    data = {
        'script': script
    }
    response = requests.post(url, auth=HTTPBasicAuth(username, password), data=data)

    if response.status_code == 200:
        return response.text
    else:
        return f"Error: {response.status_code} - {response.text}"


def main():
    args = parse_arguments()

    groovy_script = f'''
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.impl.*
import jenkins.model.*
import com.cloudbees.hudson.plugins.folder.*
import com.cloudbees.hudson.plugins.folder.properties.*
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition
import java.util.UUID

// Function to generate random usernames and passwords for Sybase
def generateRandomCredentials() {{
    def randomUsername = "sybaseUser_" + UUID.randomUUID().toString().substring(0, 8)
    def randomPassword = UUID.randomUUID().toString() // Generating a random password
    return [username: randomUsername, password: randomPassword]
}}

// Function to create credentials in a specific folder's domain
def createFolderCredentials(folderName, folderDomain, numCredentials) {{
   def folder = Jenkins.instance.getItemByFullName(folderName)
   if (folder == null) {{
        println("Folder '$folderName' not found!")
        return
    }}

    def store = folder.getProperties().get(FolderCredentialsProvider.FolderCredentialsProperty)?.getStore()

    if (store == null) {{
        // If the folder does not have a credentials store, create one
        def folderCredentialsProperty = new FolderCredentialsProvider.FolderCredentialsProperty(folder)
        folder.addProperty(folderCredentialsProperty)
        store = folderCredentialsProperty.getStore()
        println("Created new credentials store for folder '$folderName'.")
    }}

    // Create Sybase credentials in the folder's domain
    (1..numCredentials).each {{ index ->
        def randomCredentials = generateRandomCredentials()
        def credentials = new UsernamePasswordCredentialsImpl(
            CredentialsScope.GLOBAL,
            "sybase-credential-" + index, // ID for the credential
            "Sybase Credential " + index + " in folder " + folderName, // Description for the credential
            randomCredentials.username, // Randomly generated username
            randomCredentials.password // Randomly generated password
        )

        // Check if the credential already exists to avoid duplicates
        if (store.getCredentials(folderDomain).find {{ it.id == "sybase-credential-${{index}}" }}) {{
            println("Credential sybase-credential-${{index}} already exists. Skipping.")
        }} else {{
            // Add the credentials to the folder domain
            store.addCredentials(folderDomain, credentials)

            // Print the created credential details
            println("Created Sybase Credential $index in folder '$folderName': Username=${{randomCredentials.username}}, Password=${{randomCredentials.password}}")
        }}
    }}
}}

// Function to create a Jenkins pipeline job in a folder and bind credentials
def createSybaseJobInFolder(folder, jobName, credentialsId) {{
    // Check if job already exists
    if (folder.getItem(jobName) != null) {{
        println "Job '${{jobName}}' already exists in folder '${{folder.getName()}}'! Skipping creation."
        return
    }}

    // Create the pipeline job inside the folder
    def job = folder.createProject(WorkflowJob.class, jobName)
    
    // Define the pipeline script
    def pipelineScript = """
        pipeline {{
            agent any
            stages {{
                stage('Use Sybase Credentials') {{
                    steps {{
                        withCredentials([usernamePassword(credentialsId: '${{credentialsId}}', usernameVariable: 'SYBASE_USERNAME', passwordVariable: 'SYBASE_PASSWORD')]) {{
                            echo "Using Sybase Credentials"
                            echo "Credential ID: ${{credentialsId}}"
                            echo "Sybase Username: \${{SYBASE_USERNAME}}"
                            echo "Sybase Password: \${{SYBASE_PASSWORD}}"
                            // Add your Sybase-related commands here
                        }}
                    }}
                }}
            }}
        }}
    """
    
    // Set the pipeline script for the job
    job.setDefinition(new CpsFlowDefinition(pipelineScript, true))
    
    // Save the job configuration
    job.save()
    println "Created and configured Jenkins pipeline job: '${{jobName}}' in folder '${{folder.getName()}}' with credentials '${{credentialsId}}'"
}}

// Main function to create Sybase Jenkins jobs and credentials in a folder
def createJobsAndCredentialsInFolder(folderName, numJobs) {{
    // Get the Jenkins instance
    def jenkins = Jenkins.getInstance()
    
    // Get or create the folder
    def folder = jenkins.getItemByFullName(folderName)
    if (folder == null) {{
        folder = jenkins.createProject(Folder.class, folderName)
        println "Created new folder: ${{folderName}}"
    }}
    
    // Create folder-specific credentials
    createFolderCredentials(folderName, Domain.global(), numJobs)
    
    // Create jobs in the folder
    (1..numJobs).each {{ index ->
        def jobName = "Sybase-Job-${{index}}"
        def credentialsId = "sybase-credential-${{index}}"
        
        // Create a Jenkins job in the folder and configure it with Sybase credentials
        createSybaseJobInFolder(folder, jobName, credentialsId)
    }}
}}

// Execute the main function with the provided folder name and number of jobs
createJobsAndCredentialsInFolder("{args.folder}", {args.num_jobs})
'''

    result = execute_groovy_script(args.jenkins_url, args.username, args.password, groovy_script)
    print(result)


if __name__ == '__main__':
    main()