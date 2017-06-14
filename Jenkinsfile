elifePipeline {
    def commit
    stage 'Checkout', {
        checkout scm
        commit = elifeGitRevision()
    }
 
    stage 'Project tests', {
        lock('observer--ci') {
            builderDeployRevision 'observer--ci', commit
            builderProjectTests 'observer--ci', '/srv/observer'
        }
    }

    elifeMainlineOnly {
        stage 'End2end tests', {
            elifeSpectrum(
                deploy: [
                    stackname: 'observer--end2end',
                    revision: commit,
                    folder: '/srv/observer',
                    marker: 'observer',
                ]
            )
        }
     
        stage 'Approval', {
            elifeGitMoveToBranch commit, 'approved'
        }
    }
}
