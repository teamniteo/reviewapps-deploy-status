# Heroku Review Apps deployment status
[![CircleCI](https://circleci.com/gh/niteoweb/reviewapps-deploy-status/tree/master.svg?style=svg&circle-token=5ffcd6d51ad48e0b54dda7d8f37b158e5e502059)](https://circleci.com/gh/niteoweb/reviewapps-deploy-status/tree/master)
[![GitHub marketplace](https://img.shields.io/badge/marketplace-heroku--review--app--deployment--status-blue?style=flat-square&logo=github)](https://github.com/marketplace/actions/heroku-review-app-deployment-status)

A Github Action that tests the deployment status of a Heroku Review App.


## Usage
* Include the action in the workflow
    ```yaml
    name: Review App Test

    on:
        pull_request:
            branches:
            - master

    jobs:
      review-app-test:

        runs-on: ubuntu-latest
        
        steps:
        - name: Run review-app test
          uses: niteoweb/reviewapps-deploy-status@v1.2.0
          env:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          with:
            # Checks to be performed, default is all the checks
            checks: build, response

            # Delay for the application to be built in Heroku, default is 5 seconds
            build_time_delay: 5

            # Delay for the application to load and start serving, default is 5 seconds
            load_time_delay: 5

            # Interval for the repeating checks, default is 10 seconds
            interval: 10

            # Acceptable responses for the response check, default is 200
            accepted_responses: 200

            # Max time to be spent retrying for the build check, default is 120
            deployments_timeout: 120

            # Max time to be spent retrying for the response check, default is 120
            publish_timeout: 120
    ```

> Note: Work flow should include `pull_request` event.

* `GITHUB_TOKEN` is required to communicate with Github Deployment API. Default token provided by [Github](https://help.github.com/en/articles/virtual-environments-for-github-actions#github_token-secret) can be used.
* Input description:  
    All the inputs are optional. If needed, must be provided from the workflow.

    | Name | Description | Default | 
    |---|---|---|
    | checks | Comma separated list of checks to be performed  | build, response |
    | build_time_delay | Delay for the application to be built in Heroku | 5 |
    | load_time_delay | Delay for the application to load and start serving | 5 |
    | interval | Interval for the repeating checks (in seconds) | 10 |
    | accepted_responses | Acceptable responses for the response check (comma separated) | 200  |
    | deployments_timeout | Max time to be spent retrying for the build check (in seconds) | 120 |
    | publish_timeout | Max time to be spent retrying for the response check (in seconds) | 120 |


## Workflow

```
Initialize
├── Build time delay
├── Fetch build data
├── Is `build` check included in the `checks`?
│   ├── Yes
│   │   └── Is the build status a `success`?
│   │       ├── Yes
│   │       │   └── Continue
│   │       └── No
│   │           └── Are we past the `deployments_timeout`?
│   │               ├── Yes
│   │               │   └── Fail
│   │               └── No
│   │                   └── Repeat from `Fetch build data`
│   └── No
│       └── Continue
├── Load time delay
├── Is `response` check included in the `checks`?
│   ├── Yes
│   │   ├── Do an HTTP request to the app URL.
│   │   └── Is the HTTP response in the `accepted_responses`?
│   │       └── No
│   │           └── Are we past the `publish_timeout`?
│   │               ├── Yes
│   │               │   └── Fail
│   │               └── No
│   │                   └── Repeat from `Do an HTTP request to the app URL`
│   └── No
│       └── Continue
└── Done (success)
```

## Local Development
* Create a Python virtual environment(version > 3.6).
* Activate the environment.
* Install the development dependencies:
```python
    pip install -r requirements-dev.txt
```
* Make changes.
* Test the changes:
```python
    make tests
```
* Make sure that coverage is 100%.
