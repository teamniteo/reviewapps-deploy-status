import json
import os
import unittest
from unittest import mock

import pytest
import responses
from requests import exceptions

import review_app_status


@responses.activate
@mock.patch.dict(os.environ, {"GITHUB_TOKEN": "secret"})
def test_make_github_api_request_success():

    from review_app_status import _make_github_api_request

    response_body = [{"name": "deployment1"}]
    responses.add(
        responses.GET,
        "https://foo.bar/deployments",
        body=json.dumps(response_body),
        status=200,
    )

    _make_github_api_request("https://foo.bar/deployments")
    assert len(responses.calls) == 1
    assert (
        responses.calls[0].request.headers["Accept"] == "application/vnd.github.v3+json"
    )
    assert responses.calls[0].request.headers["Authorization"] == "token secret"
    assert '{"name": "deployment1"}' in str(responses.calls[0].response.content)


@responses.activate
@mock.patch.dict(os.environ, {"GITHUB_TOKEN": "secret"})
def test_make_github_api_request_failure():

    from review_app_status import _make_github_api_request

    responses.add(responses.GET, "https://foo.bar/deployments", status=503)
    with pytest.raises(exceptions.HTTPError) as excinfo:
        _make_github_api_request("https://foo.bar/deployments")
    assert len(responses.calls) == 1
    assert (
        responses.calls[0].request.headers["Accept"] == "application/vnd.github.v3+json"
    )
    assert responses.calls[0].request.headers["Authorization"] == "token secret"
    assert (
        "503 Server Error: Service Unavailable for url: https://foo.bar/deployments"
        in str(excinfo.value)
    )


@mock.patch("review_app_status._make_github_api_request")
def test_get_deployment_status_interval_greater_failure(mock_github_request):

    from review_app_status import _get_github_deployment_status_url

    with pytest.raises(ValueError) as excinfo:
        url = _get_github_deployment_status_url(
            deployments_url="https://foo.bar/deployments",
            commit_sha="commitsha12345",
            timeout=3,
            interval=4,
        )
    assert "Interval can't be greater than deployments_timeout." in str(excinfo.value)


@mock.patch("review_app_status._make_github_api_request")
def test_get_deployment_status_url_success(mock_github_request):

    from review_app_status import _get_github_deployment_status_url

    mock_github_request.return_value = [
        {
            "sha": "commitsha12345",
            "statuses_url": "https://foo.bar/deployment/statuses/1",
        }
    ]
    url = _get_github_deployment_status_url(
        deployments_url="https://foo.bar/deployments",
        commit_sha="commitsha12345",
        timeout=2,
        interval=1,
    )
    assert url == "https://foo.bar/deployment/statuses/1"
    mock_github_request.assert_called_once_with("https://foo.bar/deployments")


@mock.patch("review_app_status._make_github_api_request")
def test_get_deployment_status_url_failure(mock_github_request, caplog):

    from review_app_status import _get_github_deployment_status_url

    mock_github_request.return_value = [
        {"sha": "commitsha123", "statuses_url": "https://foo.bar/deployment/statuses"}
    ]
    with pytest.raises(ValueError) as excinfo:
        url = _get_github_deployment_status_url(
            deployments_url="https://foo.bar/deployments",
            commit_sha="commitsha12345",
            timeout=2,
            interval=1,
        )

    assert (
        caplog.records[0].message
        == "Waiting for deployments. Will check after 1 seconds."
    )
    assert "No deployment found for the lastest commit." in str(excinfo.value)
    mock_github_request.call_count == 2


@mock.patch(
    "review_app_status._make_github_api_request",
    side_effect=[
        [],
        [
            {
                "sha": "commitsha12345",
                "statuses_url": "https://foo.bar/deployment/statuses/1",
            }
        ],
    ],
)
def test_get_deployment_pending_status(mock_github_request, caplog):

    from review_app_status import _get_github_deployment_status_url

    url = _get_github_deployment_status_url(
        "https://foo.bar/deployments", "commitsha12345", 2, 1
    )

    assert url == "https://foo.bar/deployment/statuses/1"
    assert (
        caplog.records[0].message
        == "Waiting for deployments. Will check after 1 seconds."
    )
    assert mock_github_request.call_count == 2
    expected = [
        mock.call("https://foo.bar/deployments"),
        mock.call("https://foo.bar/deployments"),
    ]
    assert mock_github_request.call_args_list == expected


@mock.patch("review_app_status._make_github_api_request")
def test_get_one_build_data_status(mock_github_request):
    from review_app_status import _get_build_data

    mock_github_request.return_value = [{"id": "1"}]

    data = _get_build_data("https://foo.bar/deployments/1/status", 10)
    assert data == {"id": "1"}
    mock_github_request.assert_called_once_with("https://foo.bar/deployments/1/status")


@mock.patch(
    "review_app_status._make_github_api_request", side_effect=[[], [{"id": "1"}]]
)
def test_get_pending_build_data_status(mock_github_request, caplog):
    from review_app_status import _get_build_data

    data = _get_build_data(url="https://foo.bar/deployments/1/status", interval=1)
    assert data == {"id": "1"}
    assert (
        caplog.records[0].message
        == "Build Status is pending. Will check after 1 seconds."
    )
    assert mock_github_request.call_count == 2
    expected = [
        mock.call("https://foo.bar/deployments/1/status"),
        mock.call("https://foo.bar/deployments/1/status"),
    ]
    assert mock_github_request.call_args_list == expected


@mock.patch("review_app_status._make_github_api_request")
def test_get_multiple_build_statuses(mock_github_request, caplog):
    from review_app_status import _get_build_data

    mock_github_request.return_value = [{"id": "1"}, {"id": "2"}]

    data = _get_build_data("https://foo.bar/deployments/1/status", 10)

    assert data == {"id": "1"}
    mock_github_request.assert_called_once_with("https://foo.bar/deployments/1/status")

    assert len(caplog.records) == 1
    assert (
        caplog.records[0].message
        == "Multiple Build Statuses found. Fetching the latest build status."
    )


@responses.activate
def test_reviewapp_deployment_success(caplog):
    from review_app_status import _check_review_app_deployment_status

    responses.add(responses.GET, "https://foo-pr-bar.com", status=200)

    _check_review_app_deployment_status("https://foo-pr-bar.com", [200, 302], 5, 5)
    assert len(responses.calls) == 1
    assert len(caplog.records) == 1
    assert caplog.records[0].message == "Review app status: 200"


@responses.activate
def test_check_review_app_status_fail(caplog):
    from review_app_status import _check_review_app_deployment_status

    responses.add(responses.GET, "https://foo-pr-bar.com", status=503)

    with pytest.raises(TimeoutError) as excinfo:
        _check_review_app_deployment_status("https://foo-pr-bar.com", [200, 302], 5, 5)

    assert len(responses.calls) == 1
    assert (
        "Did not get any of the accepted status [200, 302] in the given time."
        in str(excinfo.value)
    )
    assert caplog.records[0].message == "Review app status: 503"


@responses.activate
def test_check_review_app_status_interval_greater_failure():

    from review_app_status import _check_review_app_deployment_status

    with pytest.raises(ValueError) as excinfo:
        url = _check_review_app_deployment_status(
            review_app_url="https://foo.bar",
            accepted_responses=[200],
            timeout=3,
            interval=4,
        )

    assert "Interval can't be greater than publish_timeout." in str(excinfo.value)


@responses.activate
def test_check_review_app_custom_status_success(caplog):
    from review_app_status import _check_review_app_deployment_status

    responses.add(responses.GET, "https://foo-pr-bar.com", status=302)

    _check_review_app_deployment_status("https://foo-pr-bar.com", [200, 302], 5, 5)
    assert len(responses.calls) == 1
    assert len(caplog.records) == 1
    assert caplog.records[0].message == "Review app status: 302"


@mock.patch.dict(
    os.environ,
    {
        "INPUT_CHECKS": "build, response",
        "INPUT_BUILD_TIME_DELAY": "1",
        "INPUT_LOAD_TIME_DELAY": "1",
        "INPUT_DEPLOYMENTS_TIMEOUT": "20",
        "INPUT_PUBLISH_TIMEOUT": "20",
        "INPUT_INTERVAL": "10",
        "INPUT_ACCEPTED_RESPONSES": "200, 302",
        "GITHUB_EVENT_PATH": "./test_path",
    },
)
@mock.patch("review_app_status._check_review_app_deployment_status")
@mock.patch("review_app_status._get_github_deployment_status_url")
@mock.patch("review_app_status._get_build_data")
def test_main_success(
    mock_build_data,
    mock_deployment_status_url,
    mock_review_app_deployment,
    caplog,
    capsys,
):
    from review_app_status import main

    data = """
    {
        "repository": {"deployments_url": "http://foo.bar/deployments"},
        "pull_request": {"head": {"sha": "commit12345"}}
    }
    """

    mock_deployment_status_url.return_value = "http://foo.bar/deployment_status"
    mock_build_data.return_value = {"state": "success", "environment": "foo-pr-bar"}
    with mock.patch("builtins.open", mock.mock_open(read_data=data)) as mock_file:
        main()

    mock_file.assert_called_with("./test_path")
    mock_deployment_status_url.assert_called_once_with(
        deployments_url="http://foo.bar/deployments",
        commit_sha="commit12345",
        timeout=20,
        interval=10,
    )
    mock_build_data.assert_called_once_with(
        url="http://foo.bar/deployment_status", interval=10
    )
    mock_review_app_deployment.assert_called_once_with(
        review_app_url="https://foo-pr-bar.herokuapp.com",
        accepted_responses=[200, 302],
        timeout=20,
        interval=10,
    )

    out, err = capsys.readouterr()

    "set-output name=review_app_url::https://foo-pr-bar.herokuapp.com" in out
    "set-output name=review_app_name::foo-pr-bar" in out
    "Successful" in out


@mock.patch.dict(
    os.environ,
    {
        "INPUT_CHECKS": "build, response",
        "INPUT_BUILD_TIME_DELAY": "1",
        "INPUT_LOAD_TIME_DELAY": "1",
        "INPUT_DEPLOYMENTS_TIMEOUT": "20",
        "INPUT_PUBLISH_TIMEOUT": "20",
        "INPUT_INTERVAL": "10",
        "INPUT_ACCEPTED_RESPONSES": "200, 302",
        "GITHUB_EVENT_PATH": "./test_path",
    },
)
@mock.patch("review_app_status._check_review_app_deployment_status")
@mock.patch("review_app_status._get_github_deployment_status_url")
@mock.patch("review_app_status._get_build_data")
def test_main_failure(
    mock_build_data, mock_deployment_status_url, mock_review_app_deployment, caplog
):
    from review_app_status import main

    data = """
    {
        "repository": {"deployments_url": "http://foo.bar/deployments"},
        "pull_request": {"head": {"sha": "commit12345"}}
    }
    """

    mock_deployment_status_url.return_value = "http://foo.bar/deployment_status"
    mock_build_data.return_value = {"state": "failure", "environment": "foo-pr-bar"}
    with mock.patch("builtins.open", mock.mock_open(read_data=data)) as mock_file:
        with pytest.raises(ValueError) as excinfo:
            main()

    mock_file.assert_called_with("./test_path")
    mock_deployment_status_url.assert_called_once_with(
        deployments_url="http://foo.bar/deployments",
        commit_sha="commit12345",
        timeout=20,
        interval=10,
    )
    mock_build_data.assert_called_once_with(
        url="http://foo.bar/deployment_status", interval=10
    )

    "Review App Build state: failure" in str(excinfo.value)
    mock_review_app_deployment.assert_not_called()
