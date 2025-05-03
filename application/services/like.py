from infrastructure.database.repositories import like_repository, post_repository
from infrastructure.cache import cache_client

class LikeService:
    def __init__(self):
        self.cache = cache_client
        self.repo = like_repository
        self.post_repo = post_repository

    def liked(self, post_id, user_id):
        return self.repo.find_by({ 'user_id': user_id, 'post_id': post_id })

    def like_post(self, post_id, user_id):
        posts = self.post_repo.find_by({ 'id': post_id })

        if not posts:
            return 'Post not found'
        
        has_like = self.repo.find_by({ 'user_id': user_id, 'post_id': post_id })

        if has_like:
            return

        self.repo.like(post_id, user_id)

    def dislike_post(self, post_id, user_id):
        posts = self.post_repo.find_by({ 'id': post_id })

        if not posts:
            return 'Post not found'
        
        has_like = self.repo.find_by({ 'user_id': user_id, 'post_id': post_id })

        if not has_like:
            return
        
        self.repo.dislike(post_id, user_id)
