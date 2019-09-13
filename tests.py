
import os
import responses
import unittest
from review_app_status import ReviewAppStatus
from unittest import mock


class TestReviewAppStatus(unittest.TestCase):

    def setUp(self):
        self.rpa = ReviewAppStatus('3', '1', {'number': 17, 'repository':{
            'name': 'foo'
        }}, [200, 302])

    def test_make_url(self):
        self.assertEqual(self.rpa._make_url(), 'https://foo-pr-17.herokuapp.com')

    @responses.activate
    def test_success_opened_pull_request(self):
        responses.add(
            responses.GET, "https://foo-pr-17.herokuapp.com", status=200
        )

        self.rpa.opened_pull_request()
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            responses.calls[0].request.url, 
            'https://foo-pr-17.herokuapp.com/'
        )

    @responses.activate
    def test_404_opened_pull_request(self):
        responses.add(
            responses.GET, "https://foo-pr-17.herokuapp.com", status=404
        )

        with self.assertRaises(Exception) as err:
            self.rpa.opened_pull_request()
        
        self.assertEqual('404 Client Error: Not Found for url: https://foo-pr-17.herokuapp.com/', str(err.exception))
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            responses.calls[0].request.url, 
            'https://foo-pr-17.herokuapp.com/'
        )

    @responses.activate
    def test_timeout_opened_pull_request(self):

        responses.add(
            responses.GET, "https://foo-pr-17.herokuapp.com", status=502
        )

        with self.assertRaises(Exception) as err:
            with self.assertLogs(level='INFO') as log:
                self.rpa.opened_pull_request()                

        self.assertEqual(len(log.output), 3)
        self.assertIn('status of https://foo-pr-17.herokuapp.com is 502. will retry after 1 sec', log.output[0])
        self.assertEqual('Url Timeout', str(err.exception))
        self.assertEqual(len(responses.calls), 3)
        self.assertEqual(
            responses.calls[0].request.url, 
            'https://foo-pr-17.herokuapp.com/'
        )

    @responses.activate
    def test_success_302_opened_pull_request(self):

        responses.add(
            responses.GET, "https://foo-pr-17.herokuapp.com", status=302
        )

        self.rpa.opened_pull_request()
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            responses.calls[0].request.url, 
            'https://foo-pr-17.herokuapp.com/'
        )

    @responses.activate
    def test_success_other_pull_request_actions(self):

        responses.add(
            responses.GET, "https://foo-pr-17.herokuapp.com", status=200
        )

        with self.assertLogs(level='INFO') as log:
            self.rpa.other_pull_request_actions()
        
        self.assertEqual(len(log.output), 2)
        self.assertIn('App has been redeployed. Hence the action will wait for 3 seconds before fetching the status.', log.output[0])
        self.assertIn('status of https://foo-pr-17.herokuapp.com is 200.', log.output[1])
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            responses.calls[0].request.url, 
            'https://foo-pr-17.herokuapp.com/'
        )

    @responses.activate
    def test_404_other_pull_request_actions(self):

        responses.add(
            responses.GET, "https://foo-pr-17.herokuapp.com", status=404
        )

        with self.assertRaises(Exception) as err:
            self.rpa.other_pull_request_actions()
        
        self.assertEqual('404 Client Error: Not Found for url: https://foo-pr-17.herokuapp.com/', str(err.exception))
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            responses.calls[0].request.url, 
            'https://foo-pr-17.herokuapp.com/'
        )
