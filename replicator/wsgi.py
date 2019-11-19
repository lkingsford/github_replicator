"""WSGI interface for Gunicorn to call"""
from app import app

if __name__ == "__main__":
    app.run()
