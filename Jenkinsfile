elifePipeline {
    def commit
    stage 'Checkout', {
        checkout scm
        commit = elifeGitRevision()
    }
 
    stage 'Project tests', {
        lock('observer--ci') {
            builderDeployRevision 'observer--ci', commit
            builderProjectTests 'observer--ci', '/opt/observer'
        }
    }
}
