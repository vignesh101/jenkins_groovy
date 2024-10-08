import argparse
import requests
from requests.auth import HTTPBasicAuth

# Jenkins configuration will be set from command line arguments
JENKINS_URL = ""
JENKINS_USER = ""
JENKINS_API_TOKEN = ""
FOLDER = ""


def parse_arguments():
    global JENKINS_URL, JENKINS_USER, JENKINS_API_TOKEN, FOLDER
    parser = argparse.ArgumentParser(description='Process Jenkins credentials.')
    parser.add_argument('jenkins_url', help='Jenkins URL')
    parser.add_argument('username', help='Jenkins username')
    parser.add_argument('password', help='Jenkins password or API token')
    parser.add_argument('folder', help='Folder name')
    args = parser.parse_args()

    JENKINS_URL = args.jenkins_url
    JENKINS_USER = args.username
    JENKINS_API_TOKEN = args.password
    FOLDER = args.folder


def execute_groovy_script(script):
    """
    Execute a Groovy script on the Jenkins server.

    :param script: The Groovy script to execute
    :return: The output of the script execution
    """
    url = f"{JENKINS_URL}/scriptText"
    data = {
        'script': script
    }
    response = requests.post(url, auth=HTTPBasicAuth(JENKINS_USER, JENKINS_API_TOKEN), data=data)

    if response.status_code == 200:
        return response.text
    else:
        return f"Error: {response.status_code} - {response.text}"


def main():
    groovy_script = '''
        import jenkins.model.Jenkins
        import com.cloudbees.hudson.plugins.folder.Folder
        import com.cloudbees.plugins.credentials.CredentialsProvider
        import com.cloudbees.plugins.credentials.domains.Domain
        
        def folderName = __FOLDER_NAME__
        def deleteSybaseCredentialsInFolder(folder) {
            def credentials = CredentialsProvider.lookupCredentials(
                com.cloudbees.plugins.credentials.common.StandardCredentials,
                folder,
                null,
                null
            )
        
            def credentialsStore = folder.getProperties().get(com.cloudbees.hudson.plugins.folder.properties.FolderCredentialsProvider.FolderCredentialsProperty)?.getStore()
        
            if (credentialsStore) {
                credentials.each { credential ->
                    if (credential.id.toLowerCase().contains("sybase")) {
                        println "Deleting credential with ID: ${credential.id} in folder: ${folder.fullName}"
                        credentialsStore.removeCredentials(Domain.global(), credential)
                    }
                }
            }
        }
        
        // Function to recursively process folders
        def processFolder(item) {
            if (item instanceof Folder) {
                deleteSybaseCredentialsInFolder(item)
                item.items.each { childItem ->
                    processFolder(childItem)
                }
            }
        }
        
        // Get the specific folder
        def targetFolder = Jenkins.instance.getItemByFullName(folderName)
        
        if (targetFolder instanceof Folder) {
            processFolder(targetFolder)
            println "Finished processing folder: ${targetFolder.fullName}"
        } else {
            println "Folder not found or is not a folder: ${folderName}"
        }
        
        // Save changes
        Jenkins.instance.save()
    '''
    groovy_script = groovy_script.replace('__FOLDER_NAME__', f"'{FOLDER}'")
    result = execute_groovy_script(groovy_script)
    return result


if __name__ == '__main__':
    parse_arguments()
    result_val = main()
    print(result_val)
