from presentation.dtos import FeedQueryParams, PostCreateRequest, PostFindQueryParams
from application.services import post_service
from ..guards import cookie_required
from flask_pydantic import validate
from flask import request, jsonify
from .content import bp

@bp.route('/', methods=['GET'])
@cookie_required
@validate()
def feed(query: FeedQueryParams):
    user_id = request.user['sub']

    feed = post_service.feed(user_id, query.page, query.size)
    return jsonify({ "message": feed }), 200

@bp.route('/search', methods=['GET'])
@cookie_required
@validate()
def search(query: PostFindQueryParams):
    user_id = request.user['sub']

    find_out = post_service.search_by_keyword(query.description, user_id, query.page, query.size)
    return jsonify({ "message": find_out }), 200

@bp.route('/', methods=['POST'])
@cookie_required
@validate(form=PostCreateRequest)
def create_post(form: PostCreateRequest):
    user_id = request.user['sub']
    file = request.files.get('file')
    post_service.create_post(user_id, form.content, file)
    return jsonify({ "message": "Post created" }), 201
