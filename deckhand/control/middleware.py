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

import falcon
from oslo_config import cfg
from oslo_log import log as logging
from oslo_serialization import jsonutils as json
import six

import deckhand.context
from deckhand import errors

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class ContextMiddleware(object):

    def process_request(self, req, resp):
        """Convert authentication information into a request context.

        Generate a ``deckhand.context.RequestContext`` object from the
        available authentication headers and store in the ``context`` attribute
        of the ``req`` object.

        :param req: ``falcon`` request object that will be given the context
            object.
        :raises: falcon.HTTPUnauthorized: when value of the
            'X-Identity-Status' header is not 'Confirmed' and anonymous access
            is disallowed.
        """
        if req.headers.get('X-IDENTITY-STATUS') == 'Confirmed':
            req.context = deckhand.context.RequestContext.from_environ(req.env)
        elif CONF.allow_anonymous_access:
            req.context = deckhand.context.get_context()
        else:
            raise falcon.HTTPUnauthorized()


class HookableMiddlewareMixin(object):
    """Provides methods to extract before and after hooks from WSGI Middleware
    Prior to falcon 0.2.0b1, it's necessary to provide falcon with middleware
    as "hook" functions that are either invoked before (to process requests)
    or after (to process responses) the API endpoint code runs.
    This mixin allows the process_request and process_response methods from a
    typical WSGI middleware object to be extracted for use as these hooks, with
    the appropriate method signatures.
    """

    def as_before_hook(self):
        """Extract process_request method as "before" hook
        :return: before hook function
        """

        # Need to wrap this up in a closure because the parameter counts
        # differ
        def before_hook(req, resp, params=None):
            return self.process_request(req, resp)

        try:
            return before_hook
        except AttributeError as ex:
            # No such method, we presume.
            message_template = ("Failed to get before hook from middleware "
                                "{0} - {1}")
            message = message_template.format(self.__name__, ex.message)
            LOG.error(message)
            raise errors.DeckhandException(message)

    def as_after_hook(self):
        """Extract process_response method as "after" hook
        :return: after hook function
        """

        # Need to wrap this up in a closure because the parameter counts
        # differ
        def after_hook(req, resp, resource=None):
            return self.process_response(req, resp, resource)

        try:
            return after_hook
        except AttributeError as ex:
            # No such method, we presume.
            message_template = ("Failed to get after hook from middleware "
                                "{0} - {1}")
            message = message_template.format(self.__name__, ex.message)
            LOG.error(message)
            raise errors.DeckhandException(message)


class YAMLTranslator(HookableMiddlewareMixin, object):
    """Middleware for converting all responses (error and success) to YAML.

    ``falcon`` error exceptions use JSON formatting and headers by default.
    This middleware will intercept all responses and guarantee they are YAML
    format.

    .. note::

        This does not include the 401 Unauthorized that is raised by
        ``keystonemiddleware`` which is executed in the pipeline before
        ``falcon`` middleware.
    """

    def process_request(self, req, resp):
        """Performs content type enforcement on behalf of REST verbs."""
        valid_content_types = ['application/x-yaml']
        content_type = (req.content_type.split(';', 1)[0].strip()
                        if req.content_type else '')

        if not content_type:
            raise falcon.HTTPMissingHeader('Content-Type')
        elif content_type not in valid_content_types:
            message = (
                "Unexpected content type: {type}. Expected content types "
                "are: {expected}."
            ).format(
                type=six.b(req.content_type).decode('utf-8'),
                expected=valid_content_types
            )
            raise falcon.HTTPUnsupportedMediaType(description=message)

    def process_response(self, req, resp, resource):
        """Converts responses to ``application/x-yaml`` content type."""
        resp.set_header('Content-Type', 'application/x-yaml')

        for attr in ('body', 'data'):
            if not hasattr(resp, attr):
                continue

            resp_attr = getattr(resp, attr)

            try:
                resp_attr = json.loads(resp_attr)
            except (TypeError, ValueError):
                pass

            if isinstance(resp_attr, dict):
                setattr(resp, attr, yaml.safe_dump(resp_attr))
            elif isinstance(resp_attr, (list, tuple)):
                setattr(resp, attr, yaml.safe_dump_all(resp_attr))
