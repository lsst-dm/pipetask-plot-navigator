Pipetask Plot Navigator
============================

Overview
------------------------

See the source code [README.md](./src/README.md) for details about usage.

Local Development
------------------------

Build a local Docker image tagged as `pipetask-plot-navigator:latest`:
```
docker build -t pipetask-plot-navigator:latest ./src
```

Run an ephemeral container that can load live code changes, exposing the dashboard at http://localhost:8080 :
```
docker run --rm --name pipetask-plot-navigator \
    -p 8080:8080 \
    -v "$(pwd)/src":/pipetask-plot-navigator \
    pipetask-plot-navigator:latest \
    panel serve dashboard_gen3.py --port 8080 --dev
```

Remote Development
------------------------

Remote development is tricky, because the code is running in a container on the Kubernetes cluster. To iterate on this remote code during development, you can use the `sync_container.sh` script to copy the local source code to the running container. The full command with the namespace, source directory, and target directory arguments looks like this:

```
./sync_container.sh lsst-dm-pipetask-plot-navigator src /home/worker/app
```

Once the files are copied to the container and overwrite them, the container's running command, `panel serve ...`, will automatically restart because it is using the `--dev` option [that watches for changes to certain filetypes](https://panel.holoviz.org/user_guide/Deploy_and_Export.html). Refreshing the webpage will reload the app with the modified code. 

**Note**: If your pod is recreated for any reason, the synced code will be lost because the container image will be loaded. You will need to resync the code changes that are not already pushed to the Docker image repo.

Build
------------------------

The Pipetask Plot Navigator container image is built automatically by GitHub Actions when a commit modifying the `/src` folder is pushed to the `main` branch. See `/.github/workflows/build-pipetask-plot-navigator.yaml`. 

To reduce build time, the [GitHub Cache](https://docs.github.com/en/actions/guides/caching-dependencies-to-speed-up-workflows) system is used to mimic the way Docker caches image layers when building locally. This technique is still relatively new and [is a temporary hack](https://github.com/docker/build-push-action/blob/master/docs/advanced/cache.md#github-cache).


Deploy
------------------------

Helm can be used to directly install the app to a Kubernetes cluster using:

```
helm upgrade --install pipetask-plot-navigator charts/pipetask-plot-navigator
```

To deploy as an ArgoCD application, log in and use the ArgoCD web UI to define the application that references this git repo. The generated resource definition looks like:

```
kind: Application
apiVersion: argoproj.io/v1alpha1
metadata:
  name: pipetask-plot-navigator
  namespace: default
spec:
  destination:
    namespace: lsst-dm-pipetask-plot-navigator
    server: 'https://kubernetes.default.svc'
  project: lsst-dm
  source:
    path: charts/pipetask-plot-navigator
    repoURL: 'https://github.com/lsst-dm/pipetask-plot-navigator'
    targetRevision: main
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```
