# pipe-analysis-navigator

## Usage

I believe all necessary packages to run this should be in the shared stack.

Clone this repo, then from the repo directory, run 
```
panel serve dashboard.py --port 12345  # your favorite port number
```
Or, for the gen3 backend, run
```
panel serve dashboard_gen3.py --port 12345  # your favorite port number
```

Then tunnel to that port locally:
```
ssh -NfL localhost:12345:localhost:12345 user@lsst-devl  # your ssh info
```

Then point a browser to `localhost:12345` to open the dashboard.

In the "Repository" text entry box, enter the path to a `pipe_analysis` plots directory that has images in it; e.g., the `plots` directory inside a repo, such as `/datasets/hsc/repo/rerun/RC/w_2020_38/DM-26820/plots`.

Interaction should be straightforward.  You can multi-select the "Plots" box.  More than four will require you to scroll; it should also in principle be possible to change the display sizes of the plots if that would be helpful.

If any of the plots are miscategorized, let me know.

![](screencast.gif)

## Build & Run docker container

For example:
```
docker build -t dashboard .
docker run -it -p 12345:12345 dashboard   # for port forwarding
```
