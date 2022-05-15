from flask import Flask
import json
import zabinytemp

application = Flask(__name__)


@application.route("/")
def index():
    t, time = zabinytemp.run()
    data = {
        "isotime": time.isoformat(),
        "timestamp": int(time.timestamp()),
        "temp": t
    }
    return json.dumps(data)


@application.route("/test")
def test():
    return "test"


if __name__ == "__main__":
    application.run()
