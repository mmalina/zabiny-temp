from flask import Flask
import zabinytemp
application = Flask(__name__)

@application.route("/")
def index():
    return str(zabinytemp.temp())

if __name__ == "__main__":
    application.run()
