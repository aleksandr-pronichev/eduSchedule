import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = 'university-scheduler-secret-key-2025'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'scheduler.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
