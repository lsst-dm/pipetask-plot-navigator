#!/bin/bash -e

# Default namespace
DEFAULT_NAMESPACE="lsst-dm-pipetask-plot-navigator"
# Value of --selector= argument for obtaining target pod
POD_SELECTOR="app=pipetask-plot-navigator"
# Source directory relative to this script's path
DEFAULT_SOURCE_DIR="src"
# Target directory on remote container
DEFAULT_TARGET_DIR="/home/worker/app"

# Set the default namespace if none is provided as the first argument
NAMESPACE="$1"
if [[ "X${NAMESPACE}" == "X" ]]; then
  NAMESPACE="${DEFAULT_NAMESPACE}"
fi
# Set the default source dir if none is provided as the first argument
SOURCE_DIR="$2"
if [[ "X${SOURCE_DIR}" == "X" ]]; then
  SOURCE_DIR="${DEFAULT_SOURCE_DIR}"
fi
# Set the default target dir if none is provided as the first argument
TARGET_DIR="$3"
if [[ "X${TARGET_DIR}" == "X" ]]; then
  TARGET_DIR="${DEFAULT_TARGET_DIR}"
fi

# Move to working directory containing this script, because paths
# are assumed to be relative to its location
scriptPath="$(readlink -f "$0")"
scriptDir="$(dirname "${scriptPath}")"
cd "${scriptDir}" || exit 1

# Get the pod name
POD_ID="$(kubectl get pod -n ${NAMESPACE} --selector=${POD_SELECTOR} -o jsonpath='{.items[0].metadata.name}')"

echo "Updating source code in ${POD_ID}..."
# Generate a unique string to verify that the transfer was successful
TIMESTAMP="$(date | shasum | cut -f1 -d ' ')"
echo "${TIMESTAMP}" > "${SOURCE_DIR}/.codesync"
# Count the number of forward slashes in the source path so that
# the tar command can discard those parent directories
STRIP_NUM="$(echo "${SOURCE_DIR}" | tr '/' ' ' | wc -w)"
# Copy the files into the remote container
tar cf - "${SOURCE_DIR}" | \
    kubectl exec -i -n "${NAMESPACE}" "${POD_ID}" -- \
    tar --overwrite -xf - --strip-components="${STRIP_NUM}" -C "${TARGET_DIR}"
# Compare the remote .codesync file contents with the expected value
LASTSYNC="$(kubectl exec -it -n "${NAMESPACE}" "${POD_ID}" -- cat "${TARGET_DIR}/.codesync" | tr -d '\n' | tr -d '\r')"
# Clean up temp files
rm -f "${SOURCE_DIR}/.codesync"
if [[ "${LASTSYNC}" == "${TIMESTAMP}" ]]; then
  echo "Sync successful."
  exit 0
else
  echo "Sync failed."
  exit 1
fi
