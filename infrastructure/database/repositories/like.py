from infrastructure.database.utils.connection import get_db_connection
from .generic import GenericRepository

class LikeRepository(GenericRepository):
    def __init__(self):
        super().__init__('likes')

    def like(self, post_id, user_id):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO likes (post_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (post_id, user_id)
                )
                cur.execute(
                    "UPDATE posts SET likes = likes + 1 WHERE id = %s RETURNING likes",
                    (post_id,)
                )
                updated_likes = cur.fetchone()['likes']
            conn.commit()
        return updated_likes

    def dislike(self, post_id, user_id):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM likes WHERE post_id = %s AND user_id = %s",
                    (post_id, user_id)
                )
                cur.execute(
                    "UPDATE posts SET likes = GREATEST(likes - 1, 0) WHERE id = %s RETURNING likes",
                    (post_id,)
                )
                updated_likes = cur.fetchone()['likes']
            conn.commit()
        return updated_likes
