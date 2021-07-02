"""
This module provides tests for @as_json_l() decorator.
"""
import sys
import pytest
from werkzeug.exceptions import BadRequest
from flask import Response
from flask_json import json_response, _json_l_handler, as_json_l, ndjsonify


@pytest.fixture
def theapp(app):
    # Disable pretty print to have smaller result string
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    # Force status field to test if it will be added to JSONP response.
    # It must drop status field.
    app.config['JSON_ADD_STATUS'] = False
    app.config['JSON_JSONL_OPTIONAL'] = True
    # Initial config for the @as_json_l
    # app.config['JSON_JSONP_OPTIONAL'] = True
    app.config['JSON_JSONL_QUERY_CALLBACKS'] = ['callback', 'jsonl']
    return app


# Helper function to make a request.
def req(app, *args, **kwargs):
    return app.test_request_context(*args, **kwargs)


class TestAsJsonL(object):
    # Test: required callback in the URL query.
    def test_handler_missing_callback_required(self, app):
        with pytest.raises(TypeError):
            with req(app, '/?param=1'):
                # It must fail since callback name is not provided
                # in the 'callback' query param.
                with pytest.raises(BadRequest):
                    _json_l_handler('x')

    # Test: optional callback in the URL query.
    # It must return regular response if callback name is not provided.
    def test_handler_missing_callback_optional(self, app):
        with req(app, '/?param=1'):
            rv = _json_l_handler({'x': 1})
            assert isinstance(rv, Response)
            assert rv.json == {'x': 1, 'status': 200}

    # Test: if we pass a text then it must return it as is.
    def test_handler_text(self, app):
        with pytest.raises(TypeError):
            with req(app, '/?callback=foo'):
                r = _json_l_handler(str('hello'))

    # Test: pass json response.
    def test_handler_json(self, app):
        with req(app, '/?callback=foo'):
            r = json_response(val=100, add_status_=False, jsonl=True)
            val = _json_l_handler(r)
            res = val.get_data(as_text=True).replace(' ', '').replace('\n', '')
            assert res == 'foo({"val":100});'

            assert val.status_code == 200
            assert val.headers['Content-Type'] in ('application/x-ndjson', 'application/x-jsonl')

    # Test: simple usage, no callback; it must proceed like @as_json.
    def test_simple_no_jsonl(self, app):
        @as_json_l
        def view():
            return [dict(val=1, name='Sam')]

        with req(app, '/'):
            r = view()
            assert r.status_code == 200
            assert r.headers['Content-Type'] in ('application/x-ndjson', 'application/json-l')
            assert r.json == {'val': 1, 'name': 'Sam', 'status': 200}

    # Test: simple usage, with callback.
    def test_simple(self, app):
        @as_json_l
        def view():
            return [[dict(val=1, name='Sam')]]

        with req(app, '/?callback=foo'):
            r = view()
            assert r.status_code == 200
            assert r.headers['Content-Type'] in ('application/x-ndjson', 'application/json-l')
            # Build test value.
            param = ndjsonify([dict(val=1, name='Sam')]).get_data(as_text=True)
            if param.endswith('\n'):
               param = param[:-1]
            param = param.lstrip('[').rstrip(']'.strip('\n'))
            print(param)
            print('kkkkk')
            print('kkkkk')
            print('kkkkk')
            print('kkkkk')
            print('kkkkk')

            text = 'foo(%s);' % param
            print(text)
            print(r.get_data(as_text=True))
            assert r.get_data(as_text=True) == text

    # Test: simple usage, with alternate callback.
    # By default callback name may be 'callback' or 'jsonl'.
    def test_simple2(self, app):
        @as_json_l
        def view():
            return [[dict(val=1, name='Sam')]]

        with req(app, '/?jsonl=foo'):
            r = view()
            assert r.status_code == 200
            assert r.headers['Content-Type'] in ('application/x-ndjson', 'application/json-l')

            param = ndjsonify([dict(val=1, name='Sam')]).get_data(as_text=True)
            # In flask 0.11 it adds '\n' to the end, we don't need it here.
            if param.endswith('\n'):
                param = param[:-1]
            param = param.lstrip('[').rstrip(']'.strip('\n'))
            text = 'foo(%s);' % param
            assert r.get_data(as_text=True) == text

    # Test: @as_json_l with parameters.
    # Here we force @as_json_l to use custom callback names
    # and make it required.
    def test_complex_required(self, app):
        @as_json_l(callbacks=['boo'], )
        def view():
            return [dict(val=1, name='Sam')]

        with req(app, '/?boo=foo'):
            r = view()
            assert r.status_code == 200
            assert r.headers['Content-Type'] in ('application/x-ndjson', 'application/json-l')
            param = ndjsonify([dict(val=1, name='Sam')]).get_data(as_text=True)
            # In flask 0.11 it adds '\n' to the end, we don't need it here.
            if param.endswith('\n'):
                param = param[:-1]
            param = param.lstrip('[').rstrip(']'.strip('\n'))
            text = 'foo(%s);' % param
            print(text)
            print(r.get_data(as_text=True))
            assert r.get_data(as_text=True) == text

    # Test: simple usage, no callback; it must proceed like @as_json.
    @pytest.mark.skipif(pytest.flask_ver < (0, 11),
                        reason="requires flask >= 0.11")
    def test_simple_no_jsonl_int(self, app):
        @as_json_l
        def view():
            return 1

        with pytest.raises(TypeError):
            with req(app, '/'):
                r = view()
                assert r.status_code == 200
                assert r.headers['Content-Type'] in ('application/x-ndjson', 'application/json-l')
                assert r.json == 1

    # Test: return integer.
    @pytest.mark.skipif(pytest.flask_ver < (0, 11),
                        reason="requires flask >= 0.11")
    def test_simple_int(self, app):
        @as_json_l
        def view():
            return 1

        with pytest.raises(TypeError):
            with req(app, '/?callback=foo'):
                r = view()
                assert r.status_code == 200
                assert r.headers['Content-Type'] in ('application/x-ndjson', 'application/json-l')
                assert r.get_data(as_text=True) == 'foo(1);'

    # Test: return string.
    @pytest.mark.skipif(pytest.flask_ver < (0, 11),
                        reason="requires flask >= 0.11")
    def test_simple_str(self, app):
        @as_json_l
        def view():
            return '12\"3'

        with pytest.raises(TypeError):
            with req(app, '/?callback=foo'):
                r = view()
                assert r.status_code == 200
                assert r.headers['Content-Type'] in ('application/x-ndjson', 'application/json-l')
                assert r.get_data(as_text=True) == 'foo("12\\"3");'

    # Test: return array.
    @pytest.mark.skipif(pytest.flask_ver < (0, 11),
                        reason="requires flask >= 0.11")
    def test_simple_array(self, app):
        @as_json_l
        def view():
            return ['1', 2]

        with req(app, '/?callback=foo'):
            r = view()
            assert r.status_code == 200
            assert r.headers['Content-Type'] in ('application/x-ndjson', 'application/json-l')
            param = ndjsonify(['1', 2]).get_data(as_text=True)
            if param.endswith('\n'):
                param = param[:-1]
            param = param.lstrip('[').rstrip(']'.strip('\n'))
            text = 'foo(%s);' % param
            assert r.get_data(as_text=True) == text
