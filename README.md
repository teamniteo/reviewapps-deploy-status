# Review Apps deployment status
A Github Action that tests the deployment status of a Heroku Review App.

## Usage:
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
          uses: #TODO: After publishing the action
          env:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          with:
              interval: 10 # in seconds, optional, default is 10
              accepted_responses: 200 # comma separated status codes, optional, default is 200
    ```

> Note: Work flow should include `pull_request` event.

* `GITHUB_TOKEN` is required to communicate with Github Deployment API. Default token provided by [Github](https://help.github.com/en/articles/virtual-environments-for-github-actions#github_token-secret) can be used.
* Input description:  
    All the inputs are optional. If needed, must be provided from the workflow.

    | Name | Description | Default | 
    |---|---|---|
    | interval | Wait for this amount of seconds before retrying the build check  | 10  |
    | accepted_responses | Allow/Accept the specified status codes | 200  |

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
