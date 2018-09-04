# Example Directory #

my-book/
|__ book
    |__ common
    |__ images
    |__ master.adoc
|__ upstream/

# Example Usage #

1. Refresh your fork
  a. cd <DIRECTORY>/
  b. git checkout master
  c. git pull --rebase <REMOTE> master
  d. git push origin HEAD
2. Checkout a new branch
  a. git checkout -b <BRANCH NAME>
3. Refresh the upstream folder
  a. rm -rf upstream/$* upstream/$*.revisiong
  b. scripts/git-export "<GITHUB REPOSITORY>" <BRANCH> upstream/$*
  c. git add --all upstream
4. Commit new upstream to downstream repo
  a. git commit -a -m "<COMMIT MESSAGE>"
  b. git push origin HEAD
5. If new assemblies have been added remember to update <DIRECTORY>/master.adoc
6. If new attributes have been added remember to update <DIRECTORY>/common/attributes.adoc
7. Merge synced content
  a. Go to your fork https://<GITLAB URL>/<username>/amq-streams
  b. Click __Merge Requests__ on the left
  c. Create merge request
  d. Finalize the merge in the Downstream repo
