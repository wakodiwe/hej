"""Tests for hej.api.api_error."""

import pytest
import requests

from hej.api import api_error


class TestApiError:
    def test_connection_error(self):
        with pytest.raises(SystemExit):
            api_error(requests.ConnectionError(), "http://localhost:11434")

    def test_timeout(self):
        with pytest.raises(SystemExit):
            api_error(requests.Timeout())

    def test_http_error_with_response(self):
        resp = requests.Response()
        resp.status_code = 404
        resp._content = b'{"error": "model not found"}'
        err = requests.HTTPError(response=resp)
        with pytest.raises(SystemExit):
            api_error(err)

    def test_http_error_without_response(self):
        err = requests.HTTPError("something went wrong")
        with pytest.raises(SystemExit):
            api_error(err)

    def test_http_error_bad_json(self):
        resp = requests.Response()
        resp.status_code = 500
        resp._content = b"not valid json"
        err = requests.HTTPError(response=resp)
        with pytest.raises(SystemExit):
            api_error(err)

    def test_generic_exception(self):
        with pytest.raises(SystemExit):
            api_error(Exception("something broke"))
