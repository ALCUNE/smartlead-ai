"""Uygulama giriş noktası.

Yerel geliştirme için:  python run.py
Canlı ortam için:       gunicorn "run:app" --bind 0.0.0.0:5000
"""

from app import create_app
from config import Config

# WSGI sunucularının (gunicorn vb.) bulması gereken modül düzeyi nesne.
app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=app.config["DEBUG"],
    )
