from presentation.middlewares import initialize_middlewares
from presentation.routes.content import initialize_routes
from infrastructure.database import initialize_database
from infrastructure.blob import initialize_blob
from flask import Flask

app = Flask(__name__)

initialize_middlewares(app)
initialize_routes(app)
initialize_database()
initialize_blob()

if __name__ == "__main__":
    app.run(debug=True)
