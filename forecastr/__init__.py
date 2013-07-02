from flask import Flask, jsonify, request, Response
from trellis_api import config

import os.path

instance = os.path.abspath(os.path.join(__file__, '..', '..'))
app = Flask(__name__, instance_path=instance, instance_relative_config=True)

"""Config
"""
app.config.from_object(config.DevelopmentConfig)
# This string can be a env var, too!
#app.config.from_envvar('APPLICATION_ENV')

# Flask's DebugLogger doesn't like any of this...
if 1:
    #not app.debug
    """Logging
    """
    import logging
    from logging import getLogger

    app.logger.setLevel(app.config['LOG_LEVEL'])

    # Create a default log file (is it needed when we define app_file_handler below?)
    #logging.basicConfig(filename="../logs/application.log")
    from logging.handlers import RotatingFileHandler

    log_file = os.path.join(app.instance_path, 'logs', 'application.log')
    app_file_handler = RotatingFileHandler(filename=log_file)

    # must be set to INFO, else SQLAlchemy will log nothing
    app_file_handler.setLevel(app.config['LOG_LEVEL'])
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    app_file_handler.setFormatter(formatter)

    # Log SQLAlchemy queries
    """ Other loggers available:
    sqlalchemy.dialects - controls custom logging for SQL dialects. See the documentation of individual dialects for details.
    sqlalchemy.pool - controls connection pool logging. set to logging.INFO or lower to log connection pool checkouts/checkins.
    sqlalchemy.orm - controls logging of various ORM functions. set to logging.INFO for information on mapper configurations.
    """
    loggers = [app.logger, getLogger('sqlalchemy.engine'), getLogger('sqlalchemy.pool'), getLogger('sqlalchemy.orm')]
    for logger in loggers:
        logger.addHandler(app_file_handler)

import views, models
from models.entities import sa

sa.init_app(app)

#in a view function, I can test for results and simply call not_found()!
@app.errorhandler(404)
def not_found(error=None):
    app.logger.warn(error + request.url)

    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp

@app.errorhandler(500)
def internal_error(exception):
    app.logger.exception(exception)

    message = {
        'status': 500,
        'message': 'Internal Error: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 500

    return resp
