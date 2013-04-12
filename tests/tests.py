import unittest, logging, json, sys

try:
    import xmlrunner
except ImportError:
    pass

try:
    from StringIO import StringIO
except ImportError:
    # Python 3 Support
    from io import StringIO

sys.path.append('src')
import jsonlogger
import datetime

class TestJsonLogger(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger('logging-test')
        self.logger.setLevel(logging.DEBUG)
        self.buffer = StringIO()

        self.logHandler = logging.StreamHandler(self.buffer)
        self.logger.addHandler(self.logHandler)

    def testLogException(self):
        '''
        !!! WARNING !!!
        This test ensures proper exception capture, so adjusting the code may alter
        stack traces and break this test
        '''
        fr = jsonlogger.JsonFormatter("%(levelname)s %(message)s")
        self.logHandler.setFormatter(fr)

        try:
            raise Exception("fubar")
        except:
            self.logger.exception("snafu")
        print self.buffer.getvalue()
        logJson = json.loads(self.buffer.getvalue())
        self.assertEqual(logJson["message"], "snafu")
        self.assertTrue(logJson['exc'])
        self.assertEqual(len(logJson['exc']['trace']),1)
        self.assertEqual(logJson['exc']['trace'][0]['fn'], 'testLogException')
        self.assertEqual(logJson['exc']['trace'][0]['ln'], 37)
        self.assertTrue(logJson['exc']['trace'][0]['file'].endswith('tests.py'))

    def testDefaultFormat(self):
        fr = jsonlogger.JsonFormatter()
        self.logHandler.setFormatter(fr)

        msg = "testing logging format"
        self.logger.info(msg)
        logJson = json.loads(self.buffer.getvalue())

        self.assertEqual(logJson["message"], msg)

    def testFormatKeys(self):
        supported_keys = [
            'asctime',
            'created',
            'filename',
            'funcName',
            'levelname',
            'levelno',
            'lineno',
            'module',
            'msecs',
            'message',
            'name',
            'pathname',
            'process',
            'processName',
            'relativeCreated',
            'thread',
            'threadName'
        ]

        log_format = lambda x : ['%({0:s})'.format(i) for i in x]
        custom_format = ' '.join(log_format(supported_keys))

        fr = jsonlogger.JsonFormatter(custom_format)
        self.logHandler.setFormatter(fr)

        msg = "testing logging format"
        self.logger.info(msg)
        log_msg = self.buffer.getvalue()
        log_json = json.loads(log_msg)

        for supported_key in supported_keys:
            if supported_key in log_json:
                self.assertTrue(True)

    def testUnknownFormatKey(self):
        fr = jsonlogger.JsonFormatter('%(unknown_key)s %(message)s')

        self.logHandler.setFormatter(fr)
        msg = "testing unknown logging format"
        try:
            self.logger.info(msg)
        except:
            self.assertTrue(False, "Should succeed")

    def testFormatParsingWithParentheses(self):
        fr = jsonlogger.JsonFormatter('(%(name)s) %(message)s')
        self.logHandler.setFormatter(fr)
        self.logger.info('some message')
        log_msg = self.buffer.getvalue()
        log_json = json.loads(log_msg)
        for key in ['name', 'message']:
            self.assertIn(key, log_json)

    def testLogADict(self):
        fr = jsonlogger.JsonFormatter()
        self.logHandler.setFormatter(fr)

        msg = {"text":"testing logging", "num": 1, 5: "9",
               "nested": {"more": "data"}}
        self.logger.info(msg)
        logJson = json.loads(self.buffer.getvalue())
        self.assertEqual(logJson.get("text"), msg["text"])
        self.assertEqual(logJson.get("num"), msg["num"])
        self.assertEqual(logJson.get("5"), msg[5])
        self.assertEqual(logJson.get("nested"), msg["nested"])
        self.assertEqual(logJson["message"], None)

    def testLogExtra(self):
        fr = jsonlogger.JsonFormatter()
        self.logHandler.setFormatter(fr)

        extra = {"text":"testing logging", "num": 1, 5: "9",
               "nested": {"more": "data"}}
        self.logger.info("hello", extra=extra)
        logJson = json.loads(self.buffer.getvalue())
        self.assertEqual(logJson.get("text"), extra["text"])
        self.assertEqual(logJson.get("num"), extra["num"])
        self.assertEqual(logJson.get("5"), extra[5])
        self.assertEqual(logJson.get("nested"), extra["nested"])
        self.assertEqual(logJson["message"], "hello")

    def testJsonDefaultEncoder(self):
        fr = jsonlogger.JsonFormatter()
        self.logHandler.setFormatter(fr)

        msg = {"adate": datetime.datetime(1999, 12, 31, 23, 59)}
        self.logger.info(msg)
        logJson = json.loads(self.buffer.getvalue())
        self.assertEqual(logJson.get("adate"), "1999-12-31T23:59")

    def testJsonCustomDefault(self):
        def custom(o):
            return "very custom"
        fr = jsonlogger.JsonFormatter(json_default=custom)
        self.logHandler.setFormatter(fr)

        msg = {"adate": datetime.datetime(1999, 12, 31, 23, 59), "normal": "value"}
        self.logger.info(msg)
        logJson = json.loads(self.buffer.getvalue())
        self.assertEqual(logJson.get("adate"), "very custom")
        self.assertEqual(logJson.get("normal"), "value")

if __name__=='__main__':
    if len(sys.argv[1:]) > 0 :
        if sys.argv[1] == 'xml':
            testSuite = unittest.TestLoader().loadTestsFromTestCase(TestJsonLogger)
            xmlrunner.XMLTestRunner(output='reports').run(testSuite)
    else:
        unittest.main()
