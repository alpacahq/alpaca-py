#!/usr/bin/env bash

set -e

#make sure we're in the root of our repo
pushd "$(dirname "$0")"/../../docs >>/dev/null

set +e

#clean any local files to prevent cached errors
poetry run make clean

#run make html with a flag to make sphinx treat warnings as errors instead of generating incomplete docs
#we also run doctest to ensure any doctests are successful before generating html
poetry run make html doctest SPHINXOPTS="-W"
