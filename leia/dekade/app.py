from flask import Blueprint, Flask, render_template
from flask_cors import CORS
import json
import mimetypes


mimetypes.add_type("text/javascript", ".js")


class DEKADE(Flask):

    def __init__(self):
        super().__init__(__name__, static_folder="static/", template_folder="templates/")
        CORS(self)

        self.register_blueprint(DEKADEBlueprint(self))


class DEKADEBlueprint(Blueprint):

    def __init__(self, app: DEKADE):
        super().__init__(__name__, __name__, static_folder=app.static_folder, template_folder=app.template_folder)
        self.app = app

        self.add_url_rule("/", endpoint=None, view_func=self.index, methods=["GET"])
        self.add_url_rule("/api", endpoint=None, view_func=self.api, methods=["GET"])
        self.add_url_rule("/handlebars/<template>", endpoint=None, view_func=self.handlebars_template, methods=["GET"])

    def read_template(self, name: str) -> str:
        with open("%s/%s" % (self.template_folder, name), "r") as f:
            return f.read()

    def index(self):
        return render_template("jinja/index.html", thing=123)

    def api(self):
        return json.dumps({"thing": 456})

    def handlebars_template(self, template: str):
        return self.read_template("handlebars/%s" % template)


if __name__ == "__main__":


    app = DEKADE()
    app.run("", 5000)