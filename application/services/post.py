from infrastructure.database.repositories import post_repository, like_repository
from infrastructure.cache import cache_client
from infrastructure.blob import blob_client
from infrastructure.bus import bus_client
from datetime import datetime
import msgpack
import base64
import uuid
import os

class PostService:
    def __init__(self):
        self.repo = post_repository
        self.like_repo = like_repository
        self.cache = cache_client
        self.bus = bus_client

    def _get_image_blob(self, key: str) -> str:
        response = blob_client.get_object(
            Bucket=os.getenv('BLOB_BUCKET_NAME'),
            Key=key
        )
        image_data = response['Body'].read()
        extension = os.path.splitext(key)[1][1:]

        return f"data:image/{extension};base64,{base64.b64encode(image_data).decode('utf-8')}"
    
    def update_feed_post_follow(self, user_id, following_id):
        user_feed_raw = self.cache.lrange(f"users:feed:{user_id}", 0, -1)
        other_feed_raw = self.cache.lrange(f"users:feed:{following_id}", 0, -1)

        user_feed = []
        for post in user_feed_raw:
            try:
                user_feed.append(msgpack.unpackb(post, raw=False))
            except (msgpack.exceptions.UnpackException, KeyError):
                continue

        other_feed = []
        for post in other_feed_raw:
            try:
                unpacked = msgpack.unpackb(post, raw=False)
                if unpacked.get('author_id') != user_id:
                    other_feed.append(unpacked)
            except (msgpack.exceptions.UnpackException, KeyError):
                continue

        merged_feed = sorted(
            user_feed + other_feed,
            key=lambda x: x['created_at'],
            reverse=True
        )

        packed_feed = [msgpack.packb(post, use_bin_type=True) for post in merged_feed]

        feed_key = f"users:feed:{user_id}"
        with self.cache.pipeline() as pipe:
            pipe.delete(feed_key)
            if packed_feed:
                pipe.rpush(feed_key, *packed_feed)
            pipe.execute()

    def update_feed_post_unfollow(self, user_id, unfollowed_id):
        feed_key = f"users:feed:{user_id}"

        current_feed_raw = self.cache.lrange(feed_key, 0, -1)
        current_feed = [msgpack.unpackb(post, raw=False) for post in current_feed_raw]
        filtered_feed = [post for post in current_feed if post.get('author_id') != unfollowed_id]
        packed_feed = [msgpack.packb(post, use_bin_type=True) for post in filtered_feed]

        with self.cache.pipeline() as pipe:
            pipe.delete(feed_key)
            if packed_feed:
                pipe.rpush(feed_key, *packed_feed)
            pipe.execute()

    
    def _update_feeds(self, post, followers, author_id):
        post_data = msgpack.packb({
            'id': post['id'],
            'author_id': author_id,
            'content': post['content'],
            'image_url': post['image_url'],
            'created_at': post['created_at'].timestamp()
        })
        
        with self.cache.pipeline() as pipe:
            for follower in [*followers, {'follower_id': author_id}]:
                key = f"users:feed:{follower['follower_id']}"
                pipe.lpush(key, post_data)
                pipe.ltrim(key, 0, int(os.getenv('CACHE_FEED_LIMIT')))
            pipe.execute()

    def feed(self, user_id, page=1, size=10):
        start = (page - 1) * size
        end = page * size - 1
        serialized_posts = self.cache.lrange(f"users:feed:{user_id}", start, end)

        feed = []

        for serialized in serialized_posts:
            try:
                post = msgpack.unpackb(serialized)
                post_id = post['id']
                image_blob = self._get_image_blob(post['image_url']) if post.get('image_url') else None
                total_likes = len(self.like_repo.find_by({'post_id': post_id}))
                liked = bool(self.like_repo.find_by({'post_id': post_id, 'user_id': user_id }))

                del post['image_url']

                feed.append({
                    **post,
                    'likes': total_likes,
                    'liked': liked,
                    'image_blob': image_blob,
                })

            except (msgpack.exceptions.UnpackException, KeyError) as e:
                print(f"[Feed] Erro ao processar post: {e}")
                continue

        return feed
    
    def search_by_keyword(self, terms, user_id, page=1, size=10):
        following_ids = self.bus.publish_event('death_queue', 'FOLLOWING', { 'user_id': user_id })
        parsed = [following['following_id'] for following in following_ids]

        return self.repo.search_by_description(terms, parsed, page, size)

    def create_post(self, user_id, content, file):
        unique_name = f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}_{file.filename}"

        blob_client.upload_fileobj(file, os.getenv('BLOB_BUCKET_NAME'), unique_name)
        post = self.repo.insert({
            'user_id': user_id,
            'content': content,
            'image_url': unique_name,
        })

        followers = self.bus.publish_event('death_queue', 'FOLLOWERS', { 'user_id': user_id })

        self._update_feeds(post, followers, user_id)
