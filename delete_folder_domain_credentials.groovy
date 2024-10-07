import jenkins.model.Jenkins
import com.cloudbees.hudson.plugins.folder.Folder
import com.cloudbees.plugins.credentials.CredentialsProvider
import com.cloudbees.plugins.credentials.domains.Domain

def folderName = args[0] // Get folder name from script argument

// Function to delete Sybase credentials in a folder
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