"""Tests for the HTTP Request Catcher API."""
import pytest
from app import app, all_requests, MAX_REQUEST_HISTORY


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Clear any existing requests before each test
        client.post('/__clear__')
        yield client


class TestCatchEndpoint:
    """Tests for the catch-all endpoint."""

    def test_catch_get_request(self, client):
        """Test catching a GET request."""
        response = client.get('/test-path')
        assert response.status_code == 200

    def test_catch_post_request(self, client):
        """Test catching a POST request with body."""
        response = client.post('/webhook', data='{"event": "test"}')
        assert response.status_code == 200

    def test_catch_put_request(self, client):
        """Test catching a PUT request."""
        response = client.put('/resource/123', data='updated data')
        assert response.status_code == 200

    def test_catch_delete_request(self, client):
        """Test catching a DELETE request."""
        response = client.delete('/resource/123')
        assert response.status_code == 200

    def test_catch_patch_request(self, client):
        """Test catching a PATCH request."""
        response = client.patch('/resource/123', data='{"field": "value"}')
        assert response.status_code == 200

    def test_catch_request_with_headers(self, client):
        """Test catching a request with custom headers."""
        response = client.post(
            '/webhook',
            data='test',
            headers={'X-Custom-Header': 'custom-value'}
        )
        assert response.status_code == 200

    def test_catch_returns_configured_response(self, client, monkeypatch):
        """Test returning a configured response while still capturing the request."""
        monkeypatch.setattr('app.RESPONSE_BODY', '{"success":true}')
        monkeypatch.setattr('app.RESPONSE_CONTENT_TYPE', 'application/json')
        monkeypatch.setattr('app.RESPONSE_STATUS_CODE', 202)

        response = client.post('/purge', data='request-body')

        assert response.status_code == 202
        assert response.content_type == 'application/json'
        assert response.json == {'success': True}
        assert all_requests[-1]['data'] == 'request-body'


class TestLastRequestEndpoint:
    """Tests for the /__last_request__ endpoint."""

    def test_last_request_empty(self, client):
        """Test getting last request when none have been made."""
        response = client.get('/__last_request__')
        assert response.status_code == 200
        assert response.json is None

    def test_last_request_after_single_request(self, client):
        """Test getting last request after making one request."""
        client.post('/webhook', data='test-body')
        response = client.get('/__last_request__')
        
        assert response.status_code == 200
        data = response.json
        assert data['method'] == 'POST'
        assert data['data'] == 'test-body'
        assert '/webhook' in data['url']

    def test_last_request_returns_most_recent(self, client):
        """Test that last request returns the most recent request."""
        client.post('/first', data='first')
        client.post('/second', data='second')
        client.post('/third', data='third')
        
        response = client.get('/__last_request__')
        assert response.status_code == 200
        assert '/third' in response.json['url']
        assert response.json['data'] == 'third'


class TestAllRequestsEndpoint:
    """Tests for the /__all_requests__ endpoint."""

    def test_all_requests_empty(self, client):
        """Test getting all requests when none have been made."""
        response = client.get('/__all_requests__')
        assert response.status_code == 200
        assert response.json == []

    def test_all_requests_single(self, client):
        """Test getting all requests after making one request."""
        client.post('/webhook', data='test')
        response = client.get('/__all_requests__')
        
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]['method'] == 'POST'

    def test_all_requests_multiple(self, client):
        """Test getting all requests after making multiple requests."""
        client.get('/first')
        client.post('/second', data='data')
        client.put('/third', data='update')
        
        response = client.get('/__all_requests__')
        assert response.status_code == 200
        assert len(response.json) == 3
        
        # Verify order (oldest first)
        assert '/first' in response.json[0]['url']
        assert '/second' in response.json[1]['url']
        assert '/third' in response.json[2]['url']

    def test_all_requests_preserves_headers(self, client):
        """Test that all requests preserve headers."""
        client.post(
            '/webhook',
            data='test',
            headers={'X-Test-Header': 'test-value'}
        )
        
        response = client.get('/__all_requests__')
        assert response.status_code == 200
        headers = response.json[0]['headers']
        assert headers.get('X-Test-Header') == 'test-value'


class TestFindRequestEndpoint:
    """Tests for the /__find_request__ endpoint."""

    def test_find_request_by_method(self, client):
        """Test finding requests by HTTP method."""
        client.get('/path1')
        client.post('/path2', data='data')
        client.get('/path3')
        
        response = client.get('/__find_request__?method=POST')
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]['method'] == 'POST'

    def test_find_request_by_body(self, client):
        """Test finding requests by body content."""
        client.post('/webhook', data='event-type-1')
        client.post('/webhook', data='event-type-2')
        client.post('/webhook', data='event-type-1-extended')
        
        response = client.get('/__find_request__?body=event-type-1')
        assert response.status_code == 200
        # Should match both 'event-type-1' and 'event-type-1-extended'
        assert len(response.json) == 2

    def test_find_request_by_header(self, client):
        """Test finding requests by header value."""
        client.post('/webhook', headers={'X-Request-Id': 'abc123'})
        client.post('/webhook', headers={'X-Request-Id': 'def456'})
        client.post('/webhook', headers={'X-Request-Id': 'abc123'})
        
        response = client.get('/__find_request__?header_X-Request-Id=abc123')
        assert response.status_code == 200
        assert len(response.json) == 2

    def test_find_request_by_url(self, client):
        """Test finding requests by URL content."""
        client.get('/api/users')
        client.get('/api/posts')
        client.get('/api/users/123')
        
        response = client.get('/__find_request__?url=/api/users')
        assert response.status_code == 200
        assert len(response.json) == 2

    def test_find_request_multiple_filters(self, client):
        """Test finding requests with multiple filters."""
        client.post('/webhook', data='test', headers={'X-Type': 'event'})
        client.post('/webhook', data='other', headers={'X-Type': 'event'})
        client.get('/webhook', headers={'X-Type': 'event'})
        
        response = client.get('/__find_request__?method=POST&header_X-Type=event')
        assert response.status_code == 200
        assert len(response.json) == 2
        for req in response.json:
            assert req['method'] == 'POST'

    def test_find_request_no_matches(self, client):
        """Test finding requests when no matches exist."""
        client.post('/webhook', data='test')
        
        response = client.get('/__find_request__?method=DELETE')
        assert response.status_code == 200
        assert response.json == []

    def test_find_request_case_insensitive_header(self, client):
        """Test that header matching is case-insensitive for header names."""
        client.post('/webhook', headers={'X-Custom-Header': 'value'})
        
        response = client.get('/__find_request__?header_x-custom-header=value')
        assert response.status_code == 200
        assert len(response.json) == 1


class TestClearEndpoint:
    """Tests for the /__clear__ endpoint."""

    def test_clear_with_post(self, client):
        """Test clearing requests with POST method."""
        client.post('/webhook', data='test')
        client.get('/path')
        
        response = client.post('/__clear__')
        assert response.status_code == 204
        
        # Verify requests are cleared
        all_response = client.get('/__all_requests__')
        assert all_response.json == []
        
        last_response = client.get('/__last_request__')
        assert last_response.json is None

    def test_clear_with_delete(self, client):
        """Test clearing requests with DELETE method."""
        client.post('/webhook', data='test')
        
        response = client.delete('/__clear__')
        assert response.status_code == 204
        
        # Verify requests are cleared
        all_response = client.get('/__all_requests__')
        assert all_response.json == []

    def test_clear_empty(self, client):
        """Test clearing when no requests exist."""
        response = client.post('/__clear__')
        assert response.status_code == 204


class TestRequestCapture:
    """Tests for request capture functionality."""

    def test_captures_timestamp(self, client):
        """Test that requests capture timestamp."""
        client.post('/webhook')
        
        response = client.get('/__last_request__')
        assert 'time' in response.json
        # Basic ISO format check
        assert 'T' in response.json['time']

    def test_captures_full_url(self, client):
        """Test that requests capture full URL with query params."""
        client.get('/path?param1=value1&param2=value2')
        
        response = client.get('/__last_request__')
        assert 'param1=value1' in response.json['url']
        assert 'param2=value2' in response.json['url']

    def test_captures_request_body(self, client):
        """Test that POST body is captured correctly."""
        body = '{"key": "value", "nested": {"a": 1}}'
        client.post('/webhook', data=body)
        
        response = client.get('/__last_request__')
        assert response.json['data'] == body


class TestDequeMaxLength:
    """Tests for deque max length functionality."""

    def test_max_request_history_default(self):
        """Test that MAX_REQUEST_HISTORY has a default value."""
        assert MAX_REQUEST_HISTORY > 0

    def test_deque_has_maxlen(self):
        """Test that all_requests deque has maxlen set."""
        assert all_requests.maxlen == MAX_REQUEST_HISTORY
