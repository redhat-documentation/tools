# Example Directory #

```
my-book/
|__ book
    |__ common
    |__ images
    |__ master.adoc
|__ upstream/
```

# Example Usage #

1. Refresh your fork
    1. cd <DIRECTORY>/
    2. git checkout master
    3. git pull --rebase <REMOTE> master
    4. git push origin HEAD
2. Checkout a new branch
    1. git checkout -b <BRANCH NAME>
3. Refresh the upstream folder
    1. rm -rf upstream/$* upstream/$*.revisiong
    2. scripts/git-export "<GITHUB REPOSITORY>" <BRANCH> upstream/$*
    3. git add --all upstream
4. Commit new upstream to downstream repo
    1. git commit -a -m "<COMMIT MESSAGE>"
    2. git push origin HEAD
5. If new assemblies have been added remember to update <DIRECTORY>/master.adoc
6. If new attributes have been added remember to update <DIRECTORY>/common/attributes.adoc
7. Merge synced content
    1. Go to your fork https://<GITLAB URL>/<username>/amq-streams
    2. Click __Merge Requests__ on the left
    3. Create merge request
    4. Finalize the merge in the Downstream repo
