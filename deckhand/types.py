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

DOCUMENT_SCHEMA_TYPES = (
    CERTIFICATE_SCHEMA,
    CERTIFICATE_KEY_SCHEMA,
    DATA_SCHEMA_SCHEMA,
    LAYERING_POLICY_SCHEMA,
    PASSPHRASE_SCHEMA,
    VALIDATION_POLICY_SCHEMA,
) = (
    'deckhand/Certificate',
    'deckhand/CertificateKey',
    'deckhand/DataSchema',
    'deckhand/LayeringPolicy',
    'deckhand/Passphrase',
    'deckhand/ValidationPolicy',
)


DOCUMENT_SECRET_TYPES = (
    CERTIFICATE_KEY_SCHEMA,
    CERTIFICATE_SCHEMA,
    PASSPHRASE_SCHEMA
) = (
    'deckhand/Certificate',
    'deckhand/CertificateKey',
    'deckhand/Passphrase'
)


DECKHAND_VALIDATION_TYPES = (
    DECKHAND_SCHEMA_VALIDATION,
) = (
    'deckhand-schema-validation',
)
