# Python Standard Library Imports
import os

# Phablytics Imports
from phablytics.web import application


class PhablyticsWebServer:
    """Phablytics web application server
    """
    def __init__(self):
        pass

    def run(self):
        application.run(
            host=os.environ.get('LISTEN_HOST', '::'),
            port=int(os.environ.get('PORT', '9001')),
            debug=True,
            use_reloader=False,
            threaded=False
        )


def main():
    PhablyticsWebServer().run()


if __name__ == '__main__':
    main()
