# -*- encoding: utf-8

import json
import logging
import os
import time
import typing as t
from dataclasses import dataclass
from enum import Enum, auto

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("review_app_status")


class BuildStates(Enum):
    """Expected reviewapp app build states"""

    success = "success"


class Checks(Enum):
    """Available checks"""

    # Check if the build was success
    build = auto()

    # Check the HTTP response from app URL
    response = auto()


@dataclass(frozen=True)
class Args:
    """User input arguments"""

    # Checks to be performed
    checks: t.List[Checks]

    # Delay for the application to be built in Heroku
    build_time_delay: int

    # Delay for the application to load and start serving
    load_time_delay: int

    # Interval between the repeating checks
    interval: int

    # Acceptable responses for the response check
    accepted_responses: t.List[int]

    # Max time spend retrying for the build check.
    deployments_timeout: t.List[int]


def _make_github_api_request(url: str) -> dict:
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


def _get_github_deployment_status_url(
    deployments_url: str, commit_sha: str, timeout: int, interval: int
) -> None:
    """Get deployment_status URL for the head commit.
        Inputs:
            deployments_url: This can be obtained from `pull_request` event payload.
            commit_sha: SHA of head/latest commit. This also can be obtained from `pull_request` event payload.
            timeout: Maximum waiting time to fetch the deployments.
            interval: Amount of time (in seconds) to check the deployments
                    if the deployments are not available.
        Output:
            Github deployment_status URL.
    """

    if interval > timeout:
        raise ValueError("Interval can't be greater than deployments_timeout.")

    while timeout > 0:
        deployments = _make_github_api_request(deployments_url)
        for deployment in deployments:
            if deployment["sha"] == commit_sha:
                return deployment["statuses_url"]
        time.sleep(interval)
        timeout = timeout - interval
        logger.info(f"Waiting for deployments. Will check after {interval} seconds.")

    raise ValueError("No deployment found for the lastest commit.")


def _get_build_data(url: str, interval: int) -> dict:
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


def _check_review_app_deployment_status(
    review_app_url: str, accepted_responses: t.List[int]
):
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


def main() -> None:
    """Main workflow.
    
    All the inputs are received from workflow as environment variables.
    """

    args = Args(
        checks=[Checks[x.strip()] for x in os.environ["INPUT_CHECKS"].split(",")],
        build_time_delay=int(os.environ["INPUT_BUILD_TIME_DELAY"]),
        load_time_delay=int(os.environ["INPUT_LOAD_TIME_DELAY"]),
        interval=int(os.environ["INPUT_INTERVAL"]),
        deployments_timeout=int(os.environ["INPUT_DEPLOYMENTS_TIMEOUT"]),
        accepted_responses=[
            int(x.strip()) for x in os.environ["INPUT_ACCEPTED_RESPONSES"].split(",")
        ],
    )

    # Delay the checks till the app is built
    logger.info(f"Build time delay: {args.build_time_delay} seconds")
    time.sleep(args.build_time_delay)

    logger.info(f"Statuses being accepted: {args.accepted_responses}")

    with open(os.environ["GITHUB_EVENT_PATH"]) as f:
        pull_request_data = json.load(f)

    # Fetch the GitHub status URL
    github_deployment_status_url = _get_github_deployment_status_url(
        deployments_url=pull_request_data["repository"]["deployments_url"],
        commit_sha=pull_request_data["pull_request"]["head"]["sha"],
        timeout=args.deployments_timeout,
        interval=args.interval,
    )

    # Fetch other build data
    reviewapp_build_data = _get_build_data(
        url=github_deployment_status_url, interval=args.interval
    )

    # Perform all the checks now

    if Checks.build in args.checks:
        # Check if the build was success
        build_state = reviewapp_build_data["state"]
        if build_state != BuildStates.success.value:
            raise ValueError(f"Review App Build state: {build_state}")
        
    if Checks.response in args.checks:
        # Delay the checks till the app is loads
        logger.info(f"Load time delay: {args.load_time_delay} seconds")
        time.sleep(args.load_time_delay)
        
        # Check the HTTP response from app URL
        review_app_url = f"https://{reviewapp_build_data['environment']}.herokuapp.com"
        _check_review_app_deployment_status(
            review_app_url=review_app_url, accepted_responses=args.accepted_responses
        )

    print("Successful")


if __name__ == "__main__":  # pragma: no cover
    main()
