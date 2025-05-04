from infrastructure.bus import bus_client as bus
from application.services import post_service

@bus.register_handler("UPDATE_FEED")
def update_feed(payload, ch):
    OPERATIONS = {
        "increment": post_service.update_feed_post_follow,
        "decrement": post_service.update_feed_post_unfollow,
    }

    OPERATIONS[payload['operation']](payload['user_id'], payload['following_id'])

    return 'Feed updated'
