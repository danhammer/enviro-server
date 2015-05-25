# Common tools for Google App Engine
# Copyright (C) 2014 SpaceKnow, Inc.

"""Support for making HTTP requests."""

import json
import urllib

# from google.appengine.api import urlfetch


class Response():

    """Class representing an HTTP response."""

    def __init__(self, url, response):
        self._url = url
        self._response = response

    @property
    def url(self):
        """Returns the request URL for this response."""
        return self._url

    @property
    def content(self):
        """The body content of the response."""
        return self._response.content

    @property
    def status_code(self):
        """The HTTP status code."""
        return self._response.status_code

    @property
    def headers(self):
        """The HTTP response headers, as a mapping of names to values. If
        there are multiple headers with the same name, their values will be
        joined into a single comma-separated string.
        """
        return self._response.headers

    @property
    def final_url(self):
        """The actual URL whose request returned this response. Only present
        if the fetch followed HTTP redirects. Not present if the retrieved URL
        matches the requested URL.
        """
        return self._response.final_url

    def json(self):
        """JSON. In case the JSON decoding fails, raises an exception."""
        return json.loads(self.content)


def add_url_query(url, params, method):
    """Adds urlencoded query to url using supplied params dictionary."""
    if method == 'GET' and params:
        url = '%s?%s' % (url, urllib.urlencode(params))
    return url


def get(url, params=None, method='GET', headers={}, allow_truncated=False,
        follow_redirects=True, deadline=60, validate_certificate=False):
    """makes a synchronous request to fetch a URL."""
    url = add_url_query(url, params, method)
    if params:
        params = urllib.urlencode(params)
    rpc = urlfetch.create_rpc(deadline=deadline)
    urlfetch.make_fetch_call(
        rpc, url, payload=params, method=method, headers=headers,
        allow_truncated=allow_truncated, follow_redirects=follow_redirects,
        validate_certificate=validate_certificate)
    return Response(url, rpc.get_result())
