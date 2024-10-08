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
import jenkins.model.*
import hudson.model.*
import com.cloudbees.hudson.plugins.folder.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.impl.*
import com.cloudbees.hudson.plugins.folder.properties.FolderCredentialsProvider
import org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl
import hudson.util.Secret
import java.util.UUID

// Function to generate random usernames and passwords for Sybase
def generateRandomCredentials() {{
    def randomUsername = "sybaseUser_" + UUID.randomUUID().toString().substring(0, 8)
    def randomPassword = UUID.randomUUID().toString() // Generate random password
    return [username: randomUsername, password: randomPassword]
}}

// Function to create Sybase credentials inside a folder
def createSybaseCredentialsInFolder(folder, username, password, id) {{
    def credentials = new UsernamePasswordCredentialsImpl(
        CredentialsScope.GLOBAL,
        id, // Unique ID for each credential
        "Sybase credential for Jenkins job " + id, // Description
        username, // Sybase username
        password // Sybase password
    )

    def folderCredentialsProperty = folder.properties.get(FolderCredentialsProvider.FolderCredentialsProperty)
    if (folderCredentialsProperty == null) {{
        folder.addProperty(new FolderCredentialsProvider.FolderCredentialsProperty([]))
        folderCredentialsProperty = folder.properties.get(FolderCredentialsProvider.FolderCredentialsProperty)
    }}

    folderCredentialsProperty.store.addCredentials(Domain.global(), credentials)
    println("Created Sybase Credentials: ${{id}} for Username: ${{username}} in folder: ${{folder.name}}")
}}

// Function to create a Jenkins job in a folder
def createSybaseJobInFolder(folder, jobName, credentialsId) {{
    // Check if job already exists
    if (folder.getItem(jobName) != null) {{
        println "Job ${{jobName}} already exists in folder ${{folder.name}}!"
        return
    }}

    // Create the job inside the folder
    def job = folder.createProject(FreeStyleProject, jobName)

    // Configure the job to use Jenkins' built-in credentials binding
    def bindingScript = """
        echo "Using Sybase Credentials"
        USERNAME=\\$(echo \\$SYBASE_CREDENTIALS_USR)
        PASSWORD=\\$(echo \\$SYBASE_CREDENTIALS_PSW)
        echo "Sybase Username: \\$USERNAME"
        echo "Sybase Password: \\$PASSWORD"
    """

    job.buildersList.add(new hudson.tasks.Shell(bindingScript))

    // Set up credentials binding in the job
    def credentialsBinding = new org.jenkinsci.plugins.credentialsbinding.impl.UsernamePasswordMultiBinding("SYBASE_CREDENTIALS", credentialsId)
    def buildWrappersList = job.getBuildWrappersList()
    buildWrappersList.add(new org.jenkinsci.plugins.credentialsbinding.impl.SecretBuildWrapper([credentialsBinding]))

    // Save the job
    job.save()
    println "Created and configured Jenkins job: ${{jobName}} in folder ${{folder.name}} with credentials ${{credentialsId}}"
}}

// Main function to create Sybase Jenkins jobs and credentials in a folder
def createJobsAndCredentialsInFolder(folderName, numJobs) {{
    // Get the folder where jobs and credentials will be created
    def folder = Jenkins.instance.getItemByFullName(folderName)

    if (folder == null || !(folder instanceof Folder)) {{
        println "Folder '${{folderName}}' not found!"
        return
    }}

    (1..numJobs).each {{ index ->
        def jobName = "Sybase-Job-${{index}}"
        def credentialsId = "sybase-credential-${{index}}"

        // Generate random Sybase credentials
        def randomCredentials = generateRandomCredentials()

        // Create Sybase credentials inside the folder
        createSybaseCredentialsInFolder(folder, randomCredentials.username, randomCredentials.password, credentialsId)

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
