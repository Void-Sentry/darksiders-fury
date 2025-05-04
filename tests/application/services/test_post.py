from infrastructure.database.repositories import post_repository, like_repository
from infrastructure.cache import cache_client
from application.services import post_service
from infrastructure.blob import blob_client
from infrastructure.bus import bus_client
from unittest.mock import MagicMock
from datetime import datetime
import msgpack
import base64
import pytest
import uuid
import os

class TestPostService:
    @pytest.fixture
    def mock_deps(self, monkeypatch):
        self.mocks = {
            'post_find_by': lambda *args, **kwargs: None,
            'post_insert': lambda *args, **kwargs: None,
            'post_search': lambda *args, **kwargs: [],
            'like_find_by': lambda *args, **kwargs: [],
            'cache_lrange': lambda *args, **kwargs: [],
            'cache_pipeline': MagicMock(),
            'blob_get_object': MagicMock(),
            'blob_upload': MagicMock(),
            'bus_publish': lambda *args, **kwargs: [],
            'env_values': {
                'BLOB_BUCKET_NAME': 'test-bucket',
                'CACHE_FEED_LIMIT': '1000'
            }
        }
        
        monkeypatch.setattr(post_repository, 'find_by', self.mocks['post_find_by'])
        monkeypatch.setattr(post_repository, 'insert', self.mocks['post_insert'])
        monkeypatch.setattr(post_repository, 'search_by_description', self.mocks['post_search'])
        monkeypatch.setattr(like_repository, 'find_by', self.mocks['like_find_by'])
        monkeypatch.setattr(cache_client, 'lrange', self.mocks['cache_lrange'])
        monkeypatch.setattr(cache_client, 'pipeline', self.mocks['cache_pipeline'])
        monkeypatch.setattr(blob_client, 'get_object', self.mocks['blob_get_object'])
        monkeypatch.setattr(blob_client, 'upload_fileobj', self.mocks['blob_upload'])
        monkeypatch.setattr(bus_client, 'publish_event', self.mocks['bus_publish'])
        monkeypatch.setattr(os, 'getenv', lambda key: self.mocks['env_values'].get(key))
        
        return self.mocks

    @pytest.fixture
    def service(self, mock_deps):
        return post_service

    def test_get_image_blob(self, service):
        test_key = "test_image.jpg"
        test_data = b"test_image_data"
        test_extension = "jpg"
        
        mock_response = {'Body': MagicMock()}
        mock_response['Body'].read.return_value = test_data
        self.mocks['blob_get_object'].return_value = mock_response
        
        result = service._get_image_blob(test_key)
        expected_prefix = f"data:image/{test_extension};base64,"
        
        assert result.startswith(expected_prefix)
        assert base64.b64decode(result[len(expected_prefix):]) == test_data

    def test_update_feeds(self, service):
        test_post = {
            'id': 'post1',
            'content': 'Test content',
            'image_url': 'test.jpg',
            'created_at': datetime.now()
        }
        test_followers = [{'follower_id': 'user1'}, {'follower_id': 'user2'}]
        test_author = 'author1'
        
        pipe_mock = MagicMock()
        self.mocks['cache_pipeline'].return_value.__enter__.return_value = pipe_mock
        
        service._update_feeds(test_post, test_followers, test_author)
        
        assert pipe_mock.lpush.call_count == len(test_followers) + 1
        assert pipe_mock.ltrim.call_count == len(test_followers) + 1
        pipe_mock.execute.assert_called_once()

    def test_feed_empty(self, service):
        self.mocks['cache_lrange'].return_value = []
        result = service.feed("user1")
        assert result == []

    def test_feed_with_posts(self, service):
        test_post = {
            'id': 'post1',
            'content': 'Test content',
            'image_url': 'test.jpg',
            'created_at': datetime.now()
        }
        serialized = msgpack.packb(test_post)
        
        self.mocks['cache_lrange'].return_value = [serialized]
        
        mock_response = {'Body': MagicMock()}
        mock_response['Body'].read.return_value = b"test_image_data"
        self.mocks['blob_get_object'].return_value = mock_response
        
        self.mocks['like_find_by'].side_effect = [
            [{'user_id': 'user1', 'post_id': 'post1'}],
            [{'user_id': 'user2'}, {'user_id': 'user3'}]
        ]
        
        result = service.feed("user1")
        
        assert len(result) == 1
        assert result[0]['id'] == test_post['id']
        assert result[0]['content'] == test_post['content']
        assert result[0]['liked'] is True
        assert result[0]['likes'] == 2
        assert result[0]['image_blob'] is not None

    def test_search_by_keyword(self, service):
        test_terms = "test"
        test_user = "user1"
        test_following = [{'following_id': 'user2'}, {'following_id': 'user3'}]
        test_posts = [{'id': 'post1', 'content': 'Test post'}]
        
        self.mocks['bus_publish'].return_value = test_following
        self.mocks['post_search'].return_value = test_posts
        
        result = service.search_by_keyword(test_terms, test_user)
        
        assert result == test_posts
        self.mocks['bus_publish'].assert_called_once_with('death_queue', 'FOLLOWING', {'user_id': test_user})
        self.mocks['post_search'].assert_called_once_with(test_terms, ['user2', 'user3'], 1, 10)

    def test_create_post(self, service):
        test_user = "user1"
        test_content = "Test content"
        test_file = MagicMock()
        test_file.filename = "test.jpg"
        
        test_post = {
            'id': 'post1',
            'user_id': test_user,
            'content': test_content,
            'image_url': 'test_uuid.jpg',
            'created_at': datetime.now()
        }
        self.mocks['post_insert'].return_value = test_post
        
        test_followers = [{'follower_id': 'user2'}, {'follower_id': 'user3'}]
        self.mocks['bus_publish'].return_value = test_followers
        
        service.create_post(test_user, test_content, test_file)
        
        self.mocks['blob_upload'].assert_called_once()
        self.mocks['post_insert'].assert_called_once()
        self.mocks['bus_publish'].assert_called_with('death_queue', 'FOLLOWERS', {'user_id': test_user})