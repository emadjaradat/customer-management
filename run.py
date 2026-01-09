
import os
from app import app, db

if __name__ == "__main__":
    # Create database tables
    with app.app_context():
        db.create_all()

    # Render provides PORT via environment variable
    port = int(os.environ.get("PORT", 10000))

    # Run the Flask app
    app.run(host="0.0.0.0", port=port, debug=False)
