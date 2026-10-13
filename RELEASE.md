# Release

Releases are triggered reactively by changing the version in the
`goldie/__about__.py` file. The `release.yml` workflow then creates the tag and
GitHub release, and publishes the package to PyPI and TestPyPI.

## Stable release

Open a PR against the `main` branch with the following change:

* Update the version in the `goldie/__about__.py` file (e.g., `v1.2.3`).

After the PR is merged, the `release.yml` workflow will be triggered and it
will automatically create a release and publish the package.

## Pre-release

Update the version in the `goldie/__about__.py` file to a dev version (e.g.,
`v1.2.3.dev0`) on any branch other than `main`. When the commit is pushed, the
`release.yml` workflow will be triggered and it will automatically create a
pre-release and publish the package.
