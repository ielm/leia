from flask import Blueprint
from leia.dekade.app import DEKADE

import json


class DEKADEAPIPropertiesBlueprint(Blueprint):

    def __init__(self, app: DEKADE):
        super().__init__("DEKADE-API-PROPERTIES", __name__, static_folder=app.static_folder, template_folder=app.template_folder)
        self.app = app

        self.add_url_rule("/api/knowledge/properties/children/<property>", endpoint=None, view_func=self.knowledge_properties_children, methods=["GET"])
        self.add_url_rule("/api/knowledge/properties/filter/<substring>", endpoint=None,  view_func=self.knowledge_properties_filter, methods=["GET"])
        self.add_url_rule("/api/knowledge/properties/property/<property>", endpoint=None, view_func=self.knowledge_properties_property, methods=["GET"])

    def knowledge_properties_children(self, property: str):
        property = self.app.agent.memory.properties.get_property(property)
        children = property.contains()
        children = sorted(list(map(lambda c: c.name, children)))

        return json.dumps(children)

    def knowledge_properties_filter(self, substring: str):
        substring = substring.lower()

        properties = self.app.agent.memory.properties.all()
        properties = map(lambda p: p.name, properties)
        properties = filter(lambda p: substring in p.lower(), properties)

        return json.dumps(list(sorted(properties)))

    def knowledge_properties_property(self, property: str):
        property = self.app.agent.memory.properties.get_property(property)

        return json.dumps(property.contents)
