Pipe Analysis Navigator
============================

Overview
------------------------

See the source code [Readme.md](./src/Readme.md) for details about usage.

Local Development
------------------------

Build a local Docker image tagged as `pipe-analysis-navigator:latest`:
```
docker build -t pipe-analysis-navigator:latest ./src
```

Run an ephemeral container that can load live code changes, exposing the dashboard at http://localhost:8080 :
```
docker run --rm --name pipe-analysis-navigator \
    -p 8080:8080 \
    -v "$(pwd)/src":/pipe-analysis-navigator \
    pipe-analysis-navigator:latest \
    panel serve dashboard_gen3.py --port 8080 --dev
```
Build
------------------------

The Pipe Analysis Navigator container image is built automatically by GitHub Actions when a commit modifying the `/src` folder is pushed to the `main` branch. See `/.github/workflows/build-pipe-analysis-navigator.yaml`. 

To reduce build time, the [GitHub Cache](https://docs.github.com/en/actions/guides/caching-dependencies-to-speed-up-workflows) system is used to mimic the way Docker caches image layers when building locally. This technique is still relatively new and [is a temporary hack](https://github.com/docker/build-push-action/blob/master/docs/advanced/cache.md#github-cache).


Deploy
------------------------

Helm can be used to directly install the app to a Kubernetes cluster using:

```
helm upgrade --install pipe-analysis-navigator charts/pipe-analysis-navigator
```

To deploy as an ArgoCD application, log in and use the ArgoCD web UI to define the application that references this git repo. The generated resource definition looks like:

```
kind: Application
apiVersion: argoproj.io/v1alpha1
metadata:
  name: pipe-analysis-navigator
  namespace: default
spec:
  destination:
    namespace: lsst-dm-pipe-analysis-navigator
    server: 'https://kubernetes.default.svc'
  project: lsst-dm
  source:
    path: charts/pipe-analysis-navigator
    repoURL: 'https://github.com/lsst-dm/pipe-analysis-navigator'
    targetRevision: main
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```
