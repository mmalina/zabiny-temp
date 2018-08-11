from flask import Flask
import zabinytemp
application = Flask(__name__)

@application.route("/")
def index():
    return str(zabinytemp.run()[0])

@application.route("/test")
def test():
    return 'test'

if __name__ == "__main__":
    application.run()
