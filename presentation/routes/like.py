from application.services import like_service
from ..dtos import PostInteractionRequest
from ..guards import cookie_required
from flask_pydantic import validate
from flask import request, jsonify
from flask import jsonify
from .content import bp

@bp.route('/<string:post_id>/like', methods=['POST'])
@cookie_required
@validate()
def like_post(post_id: str):
    validation = PostInteractionRequest(post_id=post_id)

    user_id = request.user['sub']
    like_service.like_post(validation.post_id, user_id)
    return jsonify({"message": f"Post {validation.post_id} User {user_id} liked"}), 201

@bp.route('/<string:post_id>/dislike', methods=['DELETE'])
@cookie_required
@validate()
def dislike_post(post_id: str):
    validation = PostInteractionRequest(post_id=post_id)

    user_id = request.user['sub']
    like_service.dislike_post(validation.post_id, user_id)
    return jsonify({"message": f"Post {validation.post_id} User {user_id} disliked"}), 201
