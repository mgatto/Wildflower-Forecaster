# Because we're using a virtualenv
activate_this = '/srv/www/api.local/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

#add the root directory of this wsgi app
import site
site.addsitedir('/srv/www/api.local/web/current')

#per environment configuration
os.environ['YOURAPPLICATION_CONFIG'] = '/var/www/yourapplication/application.cfg'

from trellis_api import app as application

