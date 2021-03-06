# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import yaml

import mock

from deckhand.tests.unit.control import base as test_base


class TestYAMLTranslator(test_base.BaseControllerTest):

    def test_request_with_correct_content_type(self):
        resp = self.app.simulate_get(
            '/versions', headers={'Content-Type': 'application/x-yaml'})
        self.assertEqual(200, resp.status_code)

    def test_request_with_correct_content_type_plus_encoding(self):
        resp = self.app.simulate_get(
            '/versions',
            headers={'Content-Type': 'application/x-yaml;encoding=utf-8'})
        self.assertEqual(200, resp.status_code)


class TestYAMLTranslatorNegative(test_base.BaseControllerTest):

    def test_request_without_content_type_raises_exception(self):
        resp = self.app.simulate_get('/versions')
        self.assertEqual(400, resp.status_code)

        expected = {
            'apiVersion': mock.ANY,
            'code': '400 Bad Request',
            'details': {
                'errorCount': 1,
                'errorType': 'HTTPMissingHeader',
                'messageList': [{
                    'error': True,
                    'message': "The Content-Type header is required."
                }]
            },
            'kind': 'status',
            'message': "The Content-Type header is required.",
            'metadata': {},
            'reason': 'Missing header value',
            'retry': False,
            'status': 'Failure'
        }
        self.assertEqual(expected, yaml.safe_load(resp.content))

    def test_request_with_invalid_content_type_raises_exception(self):
        resp = self.app.simulate_get(
            '/versions', headers={'Content-Type': 'application/json'})
        self.assertEqual(415, resp.status_code)

        expected = {
            'apiVersion': mock.ANY,
            'code': '415 Unsupported Media Type',
            'details': {
                'errorCount': 1,
                'errorType': 'HTTPUnsupportedMediaType',
                'messageList': [{
                    'error': True,
                    'message': (
                        "Unexpected content type: application/json. Expected "
                        "content types are: ['application/x-yaml'].")
                }]
            },
            'kind': 'status',
            'message': ("Unexpected content type: application/json. Expected "
                        "content types are: ['application/x-yaml']."),
            'metadata': {},
            'reason': 'Unsupported media type',
            'retry': False,
            'status': 'Failure'
        }
        self.assertEqual(expected, yaml.safe_load(resp.content))

    def test_request_with_invalid_yaml_content_type_raises_exception(self):
        """Only application/x-yaml should be supported, not application/yaml,
        because it hasn't been registered as an official MIME type yet.
        """
        resp = self.app.simulate_get(
            '/versions', headers={'Content-Type': 'application/yaml'})
        self.assertEqual(415, resp.status_code)

        expected = {
            'apiVersion': 'N/A',
            'code': '415 Unsupported Media Type',
            'details': {
                'errorCount': 1,
                'errorType': 'HTTPUnsupportedMediaType',
                'messageList': [{
                    'error': True,
                    'message': (
                        "Unexpected content type: application/yaml. Expected "
                        "content types are: ['application/x-yaml'].")
                }]
            },
            'kind': 'status',
            'message': ("Unexpected content type: application/yaml. Expected "
                        "content types are: ['application/x-yaml']."),
            'metadata': {},
            'reason': 'Unsupported media type',
            'retry': False,
            'status': 'Failure'
        }
        self.assertEqual(expected, yaml.safe_load(resp.content))
