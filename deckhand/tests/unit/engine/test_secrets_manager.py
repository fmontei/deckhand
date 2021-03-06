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

import copy

from deckhand.engine import secrets_manager
from deckhand import factories
from deckhand.tests import test_utils
from deckhand.tests.unit.db import base as test_base


class TestSecretsManager(test_base.TestDbBase):

    def setUp(self):
        super(TestSecretsManager, self).setUp()
        self.mock_barbican_driver = self.patchobject(
            secrets_manager.SecretsManager, 'barbican_driver')
        self.secret_ref = 'https://path/to/fake_secret'
        self.mock_barbican_driver.create_secret.return_value = (
            {'secret_href': self.secret_ref})

        self.secrets_manager = secrets_manager.SecretsManager()
        self.factory = factories.DocumentSecretFactory()

    def _test_create_secret(self, encryption_type, secret_type):
        secret_data = test_utils.rand_password()
        secret_doc = self.factory.gen_test(
            secret_type, encryption_type, secret_data)

        created_secret = self.secrets_manager.create(secret_doc)

        if encryption_type == 'cleartext':
            self.assertIn('secret', created_secret)
            self.assertEqual(secret_data, created_secret['secret'])
        elif encryption_type == 'encrypted':
            expected_kwargs = {
                'name': secret_doc['metadata']['name'],
                'secret_type': ('private' if secret_type == 'CertificateKey'
                                else secret_type.lower()),
                'payload': secret_doc['data']
            }
            self.mock_barbican_driver.create_secret.assert_called_once_with(
                **expected_kwargs)

            self.assertIn('secret', created_secret)
            self.assertEqual(self.secret_ref, created_secret['secret'])

    def test_create_cleartext_certificate(self):
        self._test_create_secret('cleartext', 'Certificate')

    def test_create_cleartext_certificate_key(self):
        self._test_create_secret('cleartext', 'CertificateKey')

    def test_create_cleartext_passphrase(self):
        self._test_create_secret('cleartext', 'Passphrase')

    def test_create_encrypted_certificate(self):
        self._test_create_secret('encrypted', 'Certificate')

    def test_create_encrypted_certificate_key(self):
        self._test_create_secret('encrypted', 'CertificateKey')

    def test_create_encrypted_passphrase(self):
        self._test_create_secret('encrypted', 'Passphrase')


class TestSecretsSubstitution(test_base.TestDbBase):

    def setUp(self):
        super(TestSecretsSubstitution, self).setUp()
        self.document_factory = factories.DocumentFactory(1, [1])
        self.secrets_factory = factories.DocumentSecretFactory()

    def _test_secret_substitution(self, document_mapping, secret_documents,
                                  expected_data):
        payload = self.document_factory.gen_test(document_mapping,
                                                 global_abstract=False)
        bucket_name = test_utils.rand_name('bucket')
        documents = self.create_documents(
            bucket_name, secret_documents + [payload[-1]])

        expected_documents = copy.deepcopy([documents[-1]])
        expected_documents[0]['data'] = expected_data

        secret_substitution = secrets_manager.SecretsSubstitution(documents)
        substituted_docs = secret_substitution.substitute_all()

        self.assertEqual(expected_documents, substituted_docs)

    def test_secret_substitution_single_cleartext(self):
        certificate = self.secrets_factory.gen_test(
            'Certificate', 'cleartext', data={'secret': 'CERTIFICATE DATA'})
        certificate['metadata']['name'] = 'example-cert'

        document_mapping = {
            "_GLOBAL_SUBSTITUTIONS_1_": [{
                "dest": {
                    "path": ".chart.values.tls.certificate"
                },
                "src": {
                    "schema": "deckhand/Certificate/v1",
                    "name": "example-cert",
                    "path": "."
                }

            }]
        }
        expected_data = {
            'chart': {
                'values': {
                    'tls': {
                        'certificate': 'CERTIFICATE DATA'
                    }
                }
            }
        }
        self._test_secret_substitution(
            document_mapping, [certificate], expected_data)

    def test_secret_substitution_single_cleartext_with_pattern(self):
        passphrase = self.secrets_factory.gen_test(
            'Passphrase', 'cleartext', data={'secret': 'my-secret-password'})
        passphrase['metadata']['name'] = 'example-password'

        document_mapping = {
            "_GLOBAL_DATA_1_": {
                'data': {
                    'chart': {
                        'values': {
                            'some_url': (
                                'http://admin:INSERT_PASSWORD_HERE'
                                '@service-name:8080/v1')
                        }
                    }
                }
            },
            "_GLOBAL_SUBSTITUTIONS_1_": [{
                "dest": {
                    "path": ".chart.values.some_url",
                    "pattern": "INSERT_[A-Z]+_HERE"
                },
                "src": {
                    "schema": "deckhand/Passphrase/v1",
                    "name": "example-password",
                    "path": "."
                }
            }]
        }
        expected_data = {
            'chart': {
                'values': {
                    'some_url': (
                        'http://admin:my-secret-password@service-name:8080/v1')
                }
            }
        }
        self._test_secret_substitution(
            document_mapping, [passphrase], expected_data)

    def test_secret_substitution_double_cleartext(self):
        certificate = self.secrets_factory.gen_test(
            'Certificate', 'cleartext', data={'secret': 'CERTIFICATE DATA'})
        certificate['metadata']['name'] = 'example-cert'

        certificate_key = self.secrets_factory.gen_test(
            'CertificateKey', 'cleartext', data={'secret': 'KEY DATA'})
        certificate_key['metadata']['name'] = 'example-key'

        document_mapping = {
            "_GLOBAL_SUBSTITUTIONS_1_": [{
                "dest": {
                    "path": ".chart.values.tls.certificate"
                },
                "src": {
                    "schema": "deckhand/Certificate/v1",
                    "name": "example-cert",
                    "path": "."
                }

            }, {
                "dest": {
                    "path": ".chart.values.tls.key"
                },
                "src": {
                    "schema": "deckhand/CertificateKey/v1",
                    "name": "example-key",
                    "path": "."
                }

            }]
        }
        expected_data = {
            'chart': {
                'values': {
                    'tls': {
                        'certificate': 'CERTIFICATE DATA',
                        'key': 'KEY DATA'
                    }
                }
            }
        }
        self._test_secret_substitution(
            document_mapping, [certificate, certificate_key], expected_data)

    def test_secret_substitution_multiple_cleartext(self):
        certificate = self.secrets_factory.gen_test(
            'Certificate', 'cleartext', data={'secret': 'CERTIFICATE DATA'})
        certificate['metadata']['name'] = 'example-cert'

        certificate_key = self.secrets_factory.gen_test(
            'CertificateKey', 'cleartext', data={'secret': 'KEY DATA'})
        certificate_key['metadata']['name'] = 'example-key'

        passphrase = self.secrets_factory.gen_test(
            'Passphrase', 'cleartext', data={'secret': 'my-secret-password'})
        passphrase['metadata']['name'] = 'example-password'

        document_mapping = {
            "_GLOBAL_DATA_1_": {
                'data': {
                    'chart': {
                        'values': {
                            'some_url': (
                                'http://admin:INSERT_PASSWORD_HERE'
                                '@service-name:8080/v1')
                        }
                    }
                }
            },
            "_GLOBAL_SUBSTITUTIONS_1_": [{
                "dest": {
                    "path": ".chart.values.tls.certificate"
                },
                "src": {
                    "schema": "deckhand/Certificate/v1",
                    "name": "example-cert",
                    "path": "."
                }

            }, {
                "dest": {
                    "path": ".chart.values.tls.key"
                },
                "src": {
                    "schema": "deckhand/CertificateKey/v1",
                    "name": "example-key",
                    "path": "."
                }

            }, {
                "dest": {
                    "path": ".chart.values.some_url",
                    "pattern": "INSERT_[A-Z]+_HERE"
                },
                "src": {
                    "schema": "deckhand/Passphrase/v1",
                    "name": "example-password",
                    "path": "."
                }
            }]
        }
        expected_data = {
            'chart': {
                'values': {
                    'tls': {
                        'certificate': 'CERTIFICATE DATA',
                        'key': 'KEY DATA'
                    },
                    'some_url': (
                        'http://admin:my-secret-password@service-name:8080/v1')
                }
            }
        }
        self._test_secret_substitution(
            document_mapping, [certificate, certificate_key, passphrase],
            expected_data)
