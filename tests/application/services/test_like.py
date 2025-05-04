from infrastructure.database.repositories import like_repository, post_repository
from application.services import like_service
from infrastructure.cache import cache_client
from unittest.mock import MagicMock
import pytest

class TestLikeService:
    @pytest.fixture
    def mock_deps(self, monkeypatch):
        self.mocks = {
            'like_find_by': lambda *args, **kwargs: None,
            'like_dislike': lambda *args, **kwargs: None,
            'post_find_by': lambda *args, **kwargs: None,
            'like_like': lambda *args, **kwargs: None,
        }
        
        monkeypatch.setattr(like_repository, 'find_by', self.mocks['like_find_by'])
        monkeypatch.setattr(like_repository, 'like', self.mocks['like_like'])
        monkeypatch.setattr(like_repository, 'dislike', self.mocks['like_dislike'])
        monkeypatch.setattr(post_repository, 'find_by', self.mocks['post_find_by'])
        
        return self.mocks

    @pytest.fixture
    def service(self, mock_deps):
        return like_service

    def test_liked_when_not_liked(self, service):
        self.mocks['like_find_by'] = lambda *args, **kwargs: None
        result = service.liked("post1", "user1")
        assert result is None

    def test_liked_when_liked(self, service):
        expected = {'user_id': 'user1', 'post_id': 'post1'}
        self.mocks['like_find_by'] = lambda *args, **kwargs: expected
        result = service.liked("post1", "user1")
        assert result == expected

    def test_like_post_post_not_found(self, service):
        self.mocks['post_find_by'] = lambda *args, **kwargs: []
        result = service.like_post("post1", "user1")
        assert result == 'Post not found'

    def test_like_post_already_liked(self, service):
        self.mocks['post_find_by'] = lambda *args, **kwargs: [{'id': 'post1'}]
        self.mocks['like_find_by'] = lambda *args, **kwargs: {'user_id': 'user1', 'post_id': 'post1'}
        
        result = service.like_post("post1", "user1")
        assert result is None

    def test_like_post_success(self, service):
        self.mocks['post_find_by'] = lambda *args, **kwargs: [{'id': 'post1'}]
        self.mocks['like_find_by'] = lambda *args, **kwargs: None
        
        like_called = False
        def mock_like(*args, **kwargs):
            nonlocal like_called
            like_called = True
            return None
        
        self.mocks['like_like'] = mock_like
        
        result = service.like_post("post1", "user1")
        assert like_called is True
        assert result is None

    def test_dislike_post_post_not_found(self, service):
        self.mocks['post_find_by'] = lambda *args, **kwargs: []
        result = service.dislike_post("post1", "user1")
        assert result == 'Post not found'

    def test_dislike_post_not_liked(self, service):
        self.mocks['post_find_by'] = lambda *args, **kwargs: [{'id': 'post1'}]
        self.mocks['like_find_by'] = lambda *args, **kwargs: None
        
        result = service.dislike_post("post1", "user1")
        assert result is None

    def test_dislike_post_success(self, service):
        self.mocks['post_find_by'] = lambda *args, **kwargs: [{'id': 'post1'}]
        self.mocks['like_find_by'] = lambda *args, **kwargs: {'user_id': 'user1', 'post_id': 'post1'}
        
        dislike_called = False
        def mock_dislike(*args, **kwargs):
            nonlocal dislike_called
            dislike_called = True
            return None
        
        self.mocks['like_dislike'] = mock_dislike
        
        result = service.dislike_post("post1", "user1")
        assert dislike_called is True
        assert result is None