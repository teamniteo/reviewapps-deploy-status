# -*- encoding: utf-8

import json
import logging
import os
import time
from enum import Enum

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("review_app_status")


SUCCESS = "success"  # Review App Success Build state


def _make_github_api_request(url):
    """Make github API request with `deployment` event specific headers.

    Input:
        url: URL to fetch.
    Output:
        JSON Response.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {os.environ['GITHUB_TOKEN']}",
    }

    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()


def _get_github_deployment_status_url(deployments_url, commit_sha):
    """Get deployment_status URL for the head commit.
        Inputs:
            deployments_url: This can be obtained from `pull_request` event payload.
            commit_sha: SHA of head/latest commit. This also can be obtained from `pull_request` event payload.
        Output:
            Github deployment_status URL.
    """
    deployments = _make_github_api_request(deployments_url)
    for deployment in deployments:
        if deployment["sha"] == commit_sha:
            return deployment["statuses_url"]

    raise ValueError("No deployment found for the lastest commit.")


def _get_build_data(url, interval):
    """Get Review App build data using Github's `deployment_status` API.
    
        Inputs:
            url: Deployment status URL
            interval: Amount of time (in seconds) to check the build status 
                    if the status is in pending state.
        
        Output:
            Review App build data
    """
    while True:
        response = _make_github_api_request(url)

        # Heroku returns empty list until the build is Succeeded/Failed
        if len(response) < 1:
            logger.info(
                f"Build Status is pending. Will check after {interval} seconds."
            )
            time.sleep(interval)
            continue

        # When the review app expires (depending on days specified in heroku)
        # heroku returns an additional status with state `inactive`.
        # As we are checking the status as soon as app is deployed, we can ignore this case.
        if len(response) > 1:
            logger.info(
                f"Multiple Build Statuses found. Fetching the latest build status."
            )
        return response[0]


def _check_review_app_deployment_status(review_app_url, accepted_responses):
    """Check Review App deployment status code against accepted_responses.
    
    Inputs:
        review_app_url: URL of the Review App to be checked.
        accepted_responses: status codes to be accepted.
    """
    time.sleep(5)  # Let the deployment breathe.
    r = requests.get(review_app_url)
    review_app_status = r.status_code
    logger.info(f"Review app status: {review_app_status}")
    if review_app_status not in accepted_responses:
        r.raise_for_status()


def main():
    """Main workflow.
    
    All the inputs are received from workflow as environment variables.
    """
    interval_arg = int(os.environ["INPUT_INTERVAL"])
    accepted_responses_arg = os.environ["INPUT_ACCEPTED_RESPONSES"]
    event_payload_path = os.environ["GITHUB_EVENT_PATH"]

    logger.info(f"Statuses being accepted: {accepted_responses_arg}")
    accepted_responses = set(map(int, accepted_responses_arg.split(",")))

    with open(event_payload_path) as f:
        data = f.read()
    pull_request_data = json.loads(data)

    github_deployment_status_url = _get_github_deployment_status_url(
        pull_request_data["repository"]["deployments_url"],
        pull_request_data["pull_request"]["head"]["sha"],
    )

    reviewapp_build_data = _get_build_data(github_deployment_status_url, interval_arg)

    if reviewapp_build_data["state"] != SUCCESS:
        raise ValueError(f"Review App Build state: {reviewapp_build_data['state']}")

    review_app_url = f"https://{reviewapp_build_data['environment']}.herokuapp.com"

    _check_review_app_deployment_status(review_app_url, accepted_responses)

    print("Successful")


if __name__ == "__main__":  # pragma: no cover
    main()
