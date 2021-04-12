from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer
import logging

authorizer = DummyAuthorizer()
# Define a new user having full r/w permissions
authorizer.add_user('yana', 'network', 'test', perm="elradfmwMT")
authorizer.add_user('admin', 'admin', 'admin', perm="elradfmwMT")
# Define a read-only anonymous user
authorizer.add_anonymous('shared')

handler = FTPHandler
handler.authorizer = authorizer
handler.banner = 'Welcome to FTP-server'
handler.passive_ports = range(60000, 65535)
handler.active_dtp
handler.timeout = 600
handler.log_prefix = 'XXX [%(username)s]@%(remote_ip)s'
logging.basicConfig(level=logging.INFO)

server = ThreadedFTPServer(('127.0.0.1', '1027'), handler)
server.max_cons = 50
server.max_cons_per_ip = 5
server.serve_forever()