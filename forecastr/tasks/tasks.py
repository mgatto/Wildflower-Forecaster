from celery import Celery

celery = Celery('tasks', broker=app.config['BROKER_URL'], backend=app.config['CELERY_RESULT_BACKEND'])


@celery.task
def add(x, y):
    return x + y


@celery.task
def add_user_to_ldap(user_data):
    # user_data ought to be a fully inflated 'Person' SQLAlchemy object
    pass
