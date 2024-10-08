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
import java.util.UUID

// Function to generate random usernames and passwords for Sybase
def generateRandomCredentials() {{
    def randomUsername = "sybaseUser_" + UUID.randomUUID().toString().substring(0, 8)
    def randomPassword = UUID.randomUUID().toString()
    return [username: randomUsername, password: randomPassword]
}}

// Function to create Sybase credentials in a folder
def createSybaseCredentialsInFolder(folder, username, password, id) {{
    def domain = Domain.global()
    def store = folder.properties.get(FolderCredentialsProperty).domainCredentialsMap.get(domain)
    def credentials = new UsernamePasswordCredentialsImpl(
        CredentialsScope.GLOBAL,
        id,
        "Sybase credential for Jenkins job " + id,
        username,
        password
    )
    store.addCredentials(domain, credentials)
    println("Created Sybase Credentials: ${{id}} for Username: ${{username}} in folder: ${{folder.name}}")
}}

// Function to create a Jenkins job in a folder
def createSybaseJobInFolder(folder, jobName, credentialsId) {{
    def job = folder.createProject(FreeStyleProject, jobName)
    def builders = job.buildersList

    // Add a shell step that uses the credentials
    def shell = new hudson.tasks.Shell("""
        echo "Using Sybase Credentials"
        echo "Credential ID: $credentialsId"
    """)
    builders.add(shell)

    // Add credentials binding
    def bindings = new ArrayList<hudson.tasks.EcrBinding>()
    bindings.add(new hudson.tasks.UsernamePasswordBinding("SYBASE_CREDENTIALS", credentialsId))
    def wrapper = new org.jenkinsci.plugins.credentialsbinding.impl.SecretBuildWrapper(bindings)
    job.buildWrappersList.add(wrapper)

    job.save()
    println "Created and configured Jenkins job: ${{jobName}} in folder: ${{folder.name}} with credentials: ${{credentialsId}}"
}}

// Main function to create Sybase Jenkins jobs and credentials in a folder
def createJobsAndCredentialsInFolder(folderName, numJobs) {{
    def jenkins = Jenkins.getInstance()
    def folder = jenkins.getItem(folderName)

    if (folder == null || !(folder instanceof Folder)) {{
        println "Folder '${{folderName}}' not found!"
        return
    }}

    (1..numJobs).each {{ index ->
        def jobName = "Sybase-Job-${{index}}"
        def credentialsId = "sybase-credential-${{index}}"

        def randomCredentials = generateRandomCredentials()
        createSybaseCredentialsInFolder(folder, randomCredentials.username, randomCredentials.password, credentialsId)
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
