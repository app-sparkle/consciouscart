import os
from flask import Flask
from config import Config
from extensions import csrf, limiter


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")

    csrf.init_app(app)
    limiter.init_app(app)

    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.planner import planner_bp
    from routes.analysis import analysis_bp
    from routes.budget import budget_bp
    from routes.locations import locations_bp
    from routes.insights import insights_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(locations_bp)
    app.register_blueprint(insights_bp)

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        return response

    return app


app = create_app()
application = app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug_mode = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)