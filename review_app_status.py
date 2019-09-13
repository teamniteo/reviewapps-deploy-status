# -*- encoding: utf-8

"""
Background Information:
=======================

When a pull request is opened, the heroku review app deployment status
will be 502 until the app is deployed. Once deployed, the status 
changes to 200/failure status.

When the pull request is updated, a new review app is created and deployed on top
of the existing review-app. Hence, until the new app is deployed the existing
app returns PREVIOUS status.
"""

from enum import Enum

import json
import os
import logging
import time
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("review_app_status")


class actions(Enum):
    """Pull Request Actions"""

    opened = "opened"
    reopened = "reopened"


class ReviewAppStatus:
    """Tests the deploy status of a Heroku Review App

    Inputs:
        timeout: action timeout in secs.
        span: interval to check the status.
        event_data: pull_request event data.
        statuses_to_exclude: statuses which can be allowed.
    """

    def __init__(self, timeout, span, event_data, statuses_to_exclude):
        self.timeout = int(timeout)
        self.span = int(span)
        self.event_data = event_data
        self.statuses_to_exclude = statuses_to_exclude
        self.url = self._make_url()

    def _make_url(self):
        """Generates url from branch, pull request number and repository name"""
        pull_request_number = self.event_data["number"]
        github_repo_name = self.event_data["repository"]["name"]
        heroku_app_name = os.environ.get("INPUT_HEROKU_APP_NAME")

        app = heroku_app_name if heroku_app_name else github_repo_name
        return f"https://{app}-pr-{pull_request_number}.herokuapp.com"

    def opened_pull_request(self):
        """Runs when the pull request is opened/Reopened.
        
        The main purpose of having separate method for open pull request 
        is to improve the time to fetch the result. 
        """
        while self.timeout > 0:
            r = requests.get(self.url)
            status = r.status_code
            if status in self.statuses_to_exclude:
                return
            elif status in [404, 503]:  # client error and service unavailable
                r.raise_for_status()
            else:
                logger.info(
                    f"status of {self.url} is {status}. will retry after {self.span} sec"
                )
                time.sleep(self.span)
                self.timeout = self.timeout - self.span

        raise ValueError("Url Timeout")

    def other_pull_request_actions(self):
        """Runs for other pull request actions."""
        logger.info(
            f"App has been redeployed. Hence the action will wait for {self.timeout} seconds before fetching the status."
        )

        time.sleep(self.timeout)
        r = requests.get(self.url)
        status = r.status_code
        if status in self.statuses_to_exclude:
            logger.info(f"status of {self.url} is {status}.")
        else:
            r.raise_for_status()


if __name__ == "__main__":
    """All the inputs are received from workflow as environment variables."""

    timeout_arg = int(os.environ["INPUT_TIMEOUT"])
    span_arg = int(os.environ["INPUT_SPAN"])
    event_payload = os.environ["GITHUB_EVENT_PATH"]
    statuses_arg = os.environ["INPUT_STATUSES"]

    if span_arg > timeout_arg:
        raise ValueError("span value should be less than timeout.")

    statuses_to_exclude = set(map(int, statuses_arg.split(",")))

    logger.info(f"Statuses being excluded: {statuses_arg}")

    with open(event_payload) as f:
        data = f.read()

    pull_request_data = json.loads(data)

    reviewapp_status = ReviewAppStatus(
        timeout_arg, span_arg, pull_request_data, statuses_to_exclude
    )
    action = pull_request_data["action"]

    logger.info(f"Pull request Action: {action}")

    if action in [actions.opened.value, actions.reopened.value]:
        reviewapp_status.opened_pull_request()
    else:
        reviewapp_status.other_pull_request_actions()

    print("Successful")
