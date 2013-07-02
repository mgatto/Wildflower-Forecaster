import sys
sys.path.insert(0, '/srv/www/api.local/web/current')
#os.environ['YOURAPPLICATION_CONFIG'] = '/var/www/yourapplication/application.cfg'

import trellis_api

if __name__ == '__main__':
    trellis_api.app.run()
