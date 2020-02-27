import io
import os
import logging
import json

from django.conf import settings
from django.core.management import call_command
from django.template.loader import render_to_string
from django.core.management.base import BaseCommand
from rest_framework.schemas.openapi import SchemaGenerator


logger = logging.getLogger()


class Command(BaseCommand):
    help = "Generates API docs"

    def add_arguments(self, parser):
        parser.add_argument("--check", default=False, type=bool)

    def handle(self, *args, **options):
        self.generate_docs(options)

    @staticmethod
    def read_json_doc():
        output = io.StringIO()
        call_command("generateschema", "--format=openapi-json", stdout=output)
        output.seek(0)
        return output.read()

    @staticmethod
    def generate_schema():
        generator = SchemaGenerator(title='Experimenter')
        schema = generator.get_schema()
        paths = schema["paths"]
        for path in paths:
            if  "design" in path:
                paths[path]["tags"] = "design"
            else:
                paths[path]["tags"] = "experiments"
        
        return json.dumps(schema, indent=2)

    @staticmethod
    def generate_docs(options):



        #api_json = Command.read_json_doc()
        api_json = Command.generate_schema()
        docs_dir = os.path.join(settings.BASE_DIR, "docs")
        schema_json_path = os.path.join(docs_dir, "openapi-schema.json")
        swagger_html_path = os.path.join(docs_dir, "swagger-ui.html")

        if options["check"]:
            with open(schema_json_path, "r") as f:
                old_json = f.read()
                if json.loads(api_json) != json.loads(old_json):
                    raise ValueError("Api Schemas have changed and have not been updated")

        else:
            doc_rendered = render_to_string(
                "swagger-ui-template.html", context={"spec": api_json}
            )

            with open(schema_json_path, "w+") as f:
                f.write(api_json)
            with open(swagger_html_path, "w+") as f:
                f.write(doc_rendered)
                logger.info("Docs generated Successfully")
