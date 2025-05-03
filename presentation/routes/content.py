from flask import Blueprint

bp = Blueprint('content', __name__, url_prefix='/post')

def initialize_routes(app):
    from . import post, like
    app.register_blueprint(bp)