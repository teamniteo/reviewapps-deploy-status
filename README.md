# Review Apps deployment status
A Github Action that tests the deploy status of a Heroku Review App.

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
        - uses: actions/checkout@v1
        - name: Run review-app test
        uses: #TODO: After publishing the action
        with:
            heroku_app_name: heroku-pipeline-name # optional 
            timeout: 300 # optional in seconds
            span: 10 # optional in seconds
            statuses: 200, 302, 403 # optional
    ```

> Note: Work flow should include `pull_request` event.

* Input description:  
    All the inputs are optional. If needed, must be provided from the workflow.

    | Name  | Description  | Default   | 
    |---|---|---|
    | heroku_app_name | Application name in Heroku | Github repo name  |
    | timeout |  Action timeout | 300  |  
    | span | interval to check the status  | 10  |
    | statuses | statuses to pass the action  | 200  |

* If the application name in Heroku and github repository name are not same, `heroku_app_name` can be used to provide the Heroku Application name.
* Some Review Apps have restricted access. Hence `statuses` can be used to allow restricted status code (eg: 403).


## Background Information:

There are two scenarios which needs to be considered

* When a pull request is opened, the Heroku Review App deployment status will  be 502 until the app is deployed. Once deployed, the status changes to *200/failure* status.

* When the pull request is updated, a new Review App is created and deployed on top of the existing Review App. Hence, until the new app is deployed the existing app returns **PREVIOUS** status.


## Workflow:

* When a pull request is raised, Github triggers the `Github Action` with the [pull request payload](https://developer.github.com/v3/activity/events/types/#pullrequestevent)
* Using the payload, the action retrieves `pull request action(opened, edited...)`,  `branch`, `pull request number` and `repository name`.
* Based on the `branch`, `pull request number` and `repository name` Heroku review app url is generated.
* If the pull request action is `opened/reopened`, Github Action will check for the deployment status of the generated url for every **span* secs until the **timeout*.
* If the pull request is updated, Github Action will wait until the given timeout and checks for the deployment status of the generated url.
* If the app returns successful status, Github Action passes the CI.
> Note: span and timeout can be provided in the main workflow.

### TODO:
- [x] Add docker file.
- [x] Add action.yml
- [x] Add the python script.
- [x] Test with a repository.
- [x] Add tests.
- [x] Add docs.
- [ ] publish the action.
