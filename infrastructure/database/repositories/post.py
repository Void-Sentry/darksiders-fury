from infrastructure.database.utils.connection import get_db_connection
from .generic import GenericRepository
from typing import List, Dict

class PostRepository(GenericRepository):
    def __init__(self):
        super().__init__('posts')

    def feed(self, followingList: list[dict], page=1, size=10):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                following_ids = [item['following_id'] for item in followingList]

                if not following_ids:
                    return []

                placeholders = ','.join(['%s'] * len(following_ids))

                query = f"""
                    SELECT * FROM posts
                    WHERE user_id IN ({placeholders})
                    ORDER BY created_at DESC
                    OFFSET %s LIMIT %s
                """

                cur.execute(query, tuple(following_ids) + (size * (page - 1), size))
                return cur.fetchall()

    def search_by_description(
        self,
        search_terms: str,
        user_ids: List[str],
        page: int = 1,
        size: int = 10
    ) -> List[Dict]:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                terms = search_terms.split()
                conditions = []
                params = []

                if terms:
                    desc_conditions = " OR ".join(["content ILIKE %s"] * len(terms))
                    conditions.append(f"({desc_conditions})")
                    params.extend([f"%{term}%" for term in terms])

                if user_ids:
                    placeholders = ",".join(["%s"] * len(user_ids))
                    conditions.append(f"user_id IN ({placeholders})")
                    params.extend(user_ids)

                if not conditions:
                    return []
                
                where_clause = " AND ".join(conditions) if len(conditions) > 1 else conditions[0]
                
                query = f"""
                    SELECT * FROM posts
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    OFFSET %s LIMIT %s
                """
                
                params.extend([size * (page - 1), size])
                cur.execute(query, params)

                return cur.fetchall()
                
                # columns = [desc[0] for desc in cur.description]
                # return [dict(zip(columns, row)) for row in cur.fetchall()]
