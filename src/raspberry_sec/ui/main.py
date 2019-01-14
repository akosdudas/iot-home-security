from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.web import Application, RequestHandler, authenticated
from tornado.websocket import WebSocketHandler
import multiprocessing as mp
import os, sys, logging, uuid, base64, json
import cv2
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from raspberry_sec.system.zonemanager import ZoneManager
from raspberry_sec.system.main import PCARuntime, LogRuntime
from raspberry_sec.system.util import ProcessReady
from raspberry_sec.interface.producer import Type
import raspberry_sec.ui.util as secutil


class BaseHandler(RequestHandler):

    PCA_RUNTIME = 'pca'

    LOG_RUNTIME = 'log'

    ZONEMANAGER = ZoneManager()

    @staticmethod
    def get_abs_path(file: str):
        """
        :return: the absolute path to file
        """
        return os.path.abspath(os.path.join(os.path.dirname(__file__), file))

    CONFIG_PATH = get_abs_path.__func__('../../config/prod/pca_system.json')

    PASSWD_PATH = get_abs_path.__func__('resource/passwd/passwd')

    def initialize(self, shared_data):
        self.shared_data = shared_data
        self.zone_manager = ZoneManager()

    def get_log_runtime(self):
        """
        :return: None or LogRuntime object
        """
        if self.shared_data.__contains__(BaseHandler.LOG_RUNTIME):
            return self.shared_data[BaseHandler.LOG_RUNTIME]
        else:
            return None

    def get_pca_runtime(self):
        """
        :return: None or PCARuntime object
        """
        if self.shared_data.__contains__(BaseHandler.PCA_RUNTIME):
            return self.shared_data[BaseHandler.PCA_RUNTIME]
        else:
            return None

    def set_pca_runtime(self, value):
        self.shared_data[BaseHandler.PCA_RUNTIME] = value

    def get_current_user(self):
        """
        Returns secure cookie content
        """
        return self.get_secure_cookie('admin')


class MainHandler(BaseHandler):

    LOGGER = logging.getLogger('MainHandler')

    @authenticated
    def get(self):
        """
        Returns index.html
        """
        MainHandler.LOGGER.info('Handling GET message')
        self.render('index.html')


class ConfigureHandler(BaseHandler):

    LOGGER = logging.getLogger('ConfigureHandler')

    @authenticated
    def get(self):
        """
        Returns the configure.html template
        """
        ConfigureHandler.LOGGER.info('Handling GET message')
        with open(BaseHandler.CONFIG_PATH, 'r') as file:
            config = file.read()

        self.render('configure.html', configuration=config)

    @authenticated
    def post(self):
        """
        Saves the configuration
        """
        ConfigureHandler.LOGGER.info('Handling POST message')
        self.set_header('Content-Type', 'text/plain')

        new_config = self.get_argument('cfg_content')
        if new_config:
            with open(BaseHandler.CONFIG_PATH, 'w') as file:
                file.write(new_config)
            self.write('Success')
        else:
            self.write('Error')


class ControlHandler(BaseHandler):

    LOGGER = logging.getLogger('ControlHandler')

    def status(self):
        """
        Builds the dictionary the template engine will use for filling the html
        """
        status = dict()
        if self.get_pca_runtime():
            status['text'] = 'Online'
            status['start'] = 'disabled'
            status['stop'] = ''
        else:
            status['text'] = 'Offline'
            status['start'] = ''
            status['stop'] = 'disabled'
        return status

    def stop_pca(self):
        """
        Stops the service if still running
        """
        ControlHandler.LOGGER.info('Stopping PCA')
        runtime = self.get_pca_runtime()
        if runtime:
            runtime.stop()
            self.set_pca_runtime(None)

    def start_pca(self):
        """
        Starts the service
        """
        ControlHandler.LOGGER.info('Starting PCA')

        pca_runtime = PCARuntime(
            self.get_log_runtime().log_queue,
            PCARuntime.load_pca(BaseHandler.CONFIG_PATH))

        self.set_pca_runtime(pca_runtime)
        pca_runtime.start()

    @authenticated
    def get(self):
        """
        Returns control.html
        """
        ControlHandler.LOGGER.info('Handling GET message')
        status = self.status()
        self.render('control.html', status=status)

    @authenticated
    def post(self):
        """
        Controls the PCA system
        """
        ControlHandler.LOGGER.info('Handling POST message')
        self.set_header('Content-Type', 'text/plain')

        on = 'true' == self.get_argument('on')       
        zones = self.get_argument('zone')
        zone_manager = ZoneManager()
        if on:
            self.stop_pca()
            self.start_pca()
            runtime = self.get_pca_runtime()
            zone_manager.set_zones(json.loads(zones))
 
        else:
            self.stop_pca()

class ZonesHandler(BaseHandler):

    LOGGER = logging.getLogger('ZonesHandler')

    @authenticated
    def get(self):
        """
        Returns zones from JSON config
        """
        ZonesHandler.LOGGER.info('Handling GET message')
        
        with open(BaseHandler.CONFIG_PATH, 'r') as file:
            config = file.read()

        data = json.loads(config)
        self.write(data['stream_controller']['zones'])

    @authenticated
    def post(self):
        """
        Add new zone to JSON config
        """
        ZonesHandler.LOGGER.info('Handling POST message')
        
        new_zone = self.get_argument('zone') 
        BaseHandler.ZONEMANAGER.add_zone(new_zone)


    @authenticated
    def delete(self, zone):
        """
        Deleting existing zone
        """
        ZonesHandler.LOGGER.info('Handling DELETE message')

        deleted_zone = self.get_argument('zone') 
        BaseHandler.ZONEMANAGER.delete_zone(deleted_zone)

class ZoneHandler(BaseHandler):

    LOGGER = logging.getLogger('ZoneHandler')

    @authenticated
    def post(self):
        """
        Deleting existing zone
        """
        ZoneHandler.LOGGER.info('Handling DELETE message')

        deleted_zone = self.get_argument('zone')
        BaseHandler.ZONEMANAGER.delete_zone(deleted_zone)

class FeedHandler(BaseHandler):

    LOGGER = logging.getLogger('FeedHandler')

    @authenticated
    def get(self):
        """
        Returns feed.html
        """
        FeedHandler.LOGGER.info('Handling GET message')
        runtime = self.get_pca_runtime()
        if runtime:
            producers = [p.get_name() for p in runtime.pca_system.producer_set if Type.CAMERA == p.get_type()]
        else:
            producers = []

        self.render('feed.html', producers=producers)


class FeedWebSocketHandler(WebSocketHandler, BaseHandler):

    LOGGER = logging.getLogger('FeedWebSocketHandler')

    def check_origin(self, origin):
        """
        For cross origin checking
        """
        return True

    def open(self):
        """
        On opening a websocket
        """
        FeedWebSocketHandler.LOGGER.info('Opening web-socket')
        auth = self.current_user
        if auth:
            FeedWebSocketHandler.LOGGER.info('Authenticated')
        else:
            FeedWebSocketHandler.LOGGER.warn('Not Authenticated')
            self.close()

    def img_to_str(self, img):
        """
        Converts the numpy ndarray into a HTML compatible png src
        :param img: numpy array
        :return: HTML compatible img src
        """
        resized = cv2.resize(img, (0, 0), fx=0.5, fy=0.5)
        png_encoded = cv2.imencode('.png', resized)[1]
        b64_encoded = base64.b64encode(png_encoded.tostring())
        final_format = b64_encoded.decode('utf-8')
        return '<img class="img-responsive center-block" src="data:image/png;base64,' + final_format + '">'

    def on_message(self, message):
        """
        On incoming message this method fetches an image from the given producer and sends it back
        :param message: name of the producer
        """
        FeedWebSocketHandler.LOGGER.info('Handling web-socket message')
        selected = message
        runtime = self.get_pca_runtime()

        if not runtime or not [p for p in runtime.pca_system.producer_set if p.get_name() == selected]:
            self.write_message('ERROR')
        else:
            producer = [p for p in runtime.pca_system.producer_set if p.get_name() == selected][0]
            proxy = runtime.pca_system.prod_to_proxy[producer]
            self.write_message(self.img_to_str(proxy.get_data()))

    def on_close(self):
        FeedWebSocketHandler.LOGGER.info('Closing web-socket')
        pass


class AboutHandler(BaseHandler):

    LOGGER = logging.getLogger('AboutHandler')

    @authenticated
    def get(self):
        """
        Returns about.html
        """
        AboutHandler.LOGGER.info('Handling GET message')
        self.render('about.html')


class LoginHandler(BaseHandler):

    LOGGER = logging.getLogger('LoginHandler')

    def check_credential(self, passwd: str):
        """
        Checks the password
        :param passwd: admin password
        :return: True if password is correct, False otherwise
        """
        try:
            LoginHandler.LOGGER.info('Checking credentials')
            return secutil.validate(passwd, BaseHandler.PASSWD_PATH)
        except Exception as e:
            LoginHandler.LOGGER.error(e.__str__())

    def get(self):
        """
        Returns login.html
        """
        LoginHandler.LOGGER.info('Handling GET message')
        self.render('login.html', error_msg='', next=self.get_argument('next','/'))

    @authenticated
    def delete(self):
        """
        Logs out user
        """
        LoginHandler.LOGGER.info('Handling DELETE message')
        self.clear_cookie('admin')

    def post(self):
        """
        Authenticates the user
        """
        LoginHandler.LOGGER.info('Handling POST message')
        if self.check_credential(self.get_argument('password')):
            self.set_secure_cookie('admin', 'AUTH')
            self.redirect(url=self.get_argument('next', u'/'))
        else:
            self.set_status(401)
            self.render('login.html', error_msg='Wrong password!', next=self.get_argument('next','/'))


def make_app(log_runtime: LogRuntime):
    """
    Builds the application
    :param log_runtime: holding logging related objects
    :return: http server
    """
    # Settings
    config = dict(shared_data={BaseHandler.LOG_RUNTIME: log_runtime})
    settings = {
        'template_path': 'template',
        'static_path': 'static',
        'login_url': '/login',
        'cookie_secret': base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes + uuid.uuid4().bytes),
        'xsrf_cookies': True
    }

    # Endpoints
    application = Application([
        (r'/', MainHandler, config),
        (r'/configure', ConfigureHandler, config),
        (r'/control', ControlHandler, config),
        (r'/zones', ZonesHandler, config),
        (r'/zones/.*', ZoneHandler, config),
        (r'/feed', FeedHandler, config),
        (r'/feed/websocket', FeedWebSocketHandler, config),
        (r'/about', AboutHandler, config),
        (r'/login', LoginHandler, config)],
        **settings
    )

    # Connection
    return HTTPServer(
        application,
        ssl_options = {
            'certfile': 'resource/ssl/server.crt',
            'keyfile': 'resource/ssl/server.key',
        }
    )


if __name__ == '__main__':
    mp.set_start_method('spawn')

    # Start logging process
    log_runtime = LogRuntime(level=logging.INFO)
    log_runtime.start()

    # Setup logging for current process
    ProcessReady.setup_logging(log_runtime.log_queue)

    server = make_app(log_runtime)
    server.listen(8080)
    IOLoop.current().start()

    # Stop logging process
    log_runtime.stop()
