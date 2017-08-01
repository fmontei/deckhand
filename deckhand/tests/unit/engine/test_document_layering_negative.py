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

from deckhand.engine import layering
from deckhand import errors
from deckhand.tests.unit.engine import test_document_layering


class TestDocumentLayeringNegative(
        test_document_layering.TestDocumentLayering):

    def test_layering_method_merge_key_not_in_child(self):
        kwargs = {
            "_GLOBAL_DATA_": {"data": {"a": {"x": 1, "y": 2}, "c": 9}},
            "_SITE_DATA_": {"data": {"a": {"x": 7, "z": 3}, "b": 4}},
            "_SITE_ACTIONS_": {
                "actions": [{"method": "merge", "path": ".c"}]}
        }
        documents = self._format_data(self.FAKE_YAML_DATA_2_LAYERS, kwargs)
        self._test_layering(
            documents, exception_expected=errors.MissingDocumentKey)

    def test_layering_method_delete_key_not_in_child(self):
        # The key will not be in the site after the global data is copied into
        # the site data implicitly.
        kwargs = {
            "_GLOBAL_DATA_": {"data": {"a": {"x": 1, "y": 2}, "c": 9}},
            "_SITE_DATA_": {"data": {"a": {"x": 7, "z": 3}, "b": 4}},
            "_SITE_ACTIONS_": {
                "actions": [{"method": "delete", "path": ".b"}]}
        }
        documents = self._format_data(self.FAKE_YAML_DATA_2_LAYERS, kwargs)
        self._test_layering(
            documents, exception_expected=errors.MissingDocumentKey)

    def test_layering_method_replace_key_not_in_child(self):
        kwargs = {
            "_GLOBAL_DATA_": {"data": {"a": {"x": 1, "y": 2}, "c": 9}},
            "_SITE_DATA_": {"data": {"a": {"x": 7, "z": 3}, "b": 4}},
            "_SITE_ACTIONS_": {
                "actions": [{"method": "replace", "path": ".c"}]}
        }
        documents = self._format_data(self.FAKE_YAML_DATA_2_LAYERS, kwargs)
        self._test_layering(
            documents, exception_expected=errors.MissingDocumentKey)

    def test_layering_without_layering_policy(self):
        documents = self._format_data(self.FAKE_YAML_DATA_2_LAYERS, {})
        documents.pop(0)  # First doc is layering policy.

        self.assertRaises(errors.LayeringPolicyNotFound,
                          layering.DocumentLayering, documents)

    def test_layering_with_broken_layer_order(self):
        documents = self._format_data(self.FAKE_YAML_DATA_2_LAYERS, {})
        broken_layer_orders = [
            ['site', 'region', 'global'], ['broken', 'global'], ['broken'],
            ['site', 'broken']]

        for broken_layer_order in broken_layer_orders:
            documents[0]['data']['layerOrder'] = broken_layer_order
            # The site will not be able to find a correct parent.
            self.assertRaises(errors.MissingDocumentParent,
                              layering.DocumentLayering, documents)

    def test_layering_child_with_invalid_parent_selector(self):
        documents = self._format_data(self.FAKE_YAML_DATA_2_LAYERS, {})

        for parent_selector in ({'key2': 'value2'}, {'key1': 'value2'}):
            documents[-1]['metadata']['layeringDefinition'][
                'parentSelector'] = parent_selector

            self.assertRaises(errors.MissingDocumentParent,
                              layering.DocumentLayering, documents)

    def test_layering_unreferenced_parent_label(self):
        documents = self._format_data(self.FAKE_YAML_DATA_2_LAYERS, {})

        for parent_label in ({'key2': 'value2'}, {'key1': 'value2'}):
            # Second doc is the global doc, or parent.
            documents[1]['metadata']['labels'] = [parent_label]

            self.assertRaises(errors.MissingDocumentParent,
                              layering.DocumentLayering, documents)

    def test_layering_duplicate_parent_selector_2_layer(self):
        # Validate that documents belonging to the same layer cannot have the
        # same unique parent identifier referenced by `parentSelector`.
        documents = self._format_data(self.FAKE_YAML_DATA_2_LAYERS, {})
        documents.append(documents[1])  # Copy global layer.

        self.assertRaises(errors.IndeterminateDocumentParent,
                          layering.DocumentLayering, documents)

    def test_layering_duplicate_parent_selector_3_layer(self):
        # Validate that documents belonging to the same layer cannot have the
        # same unique parent identifier referenced by `parentSelector`.
        documents = self._format_data(self.FAKE_YAML_DATA_3_LAYERS, {})

        # 1 is global layer, 2 is region layer.
        for idx in (1, 2):
            documents.append(documents[idx])
            self.assertRaises(errors.IndeterminateDocumentParent,
                              layering.DocumentLayering, documents)
            documents.pop(-1)  # Remove the just-appended duplicate.
