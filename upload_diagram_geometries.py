import json
import os
import logging
import logging.handlers

import requests
import GeodesignHub
import config
from pick import pick


class ScriptLogger:
    def __init__(self):
        self.log_file_name = "logs/latest.log"
        self.path = os.getcwd()
        self.logpath = os.path.join(self.path, "logs")
        if not os.path.exists(self.logpath):
            os.mkdir(self.logpath)
        self.logging_level = logging.INFO
        # set TimedRotatingFileHandler for root
        self.formatter = logging.Formatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s"
        )
        # use very short interval for this example, typical 'when' would be 'midnight' and no explicit interval
        self.handler = logging.handlers.TimedRotatingFileHandler(
            self.log_file_name, when="S", interval=30, backupCount=10
        )
        self.handler.setFormatter(self.formatter)
        self.logger = logging.getLogger()  # or pass string to give it a name
        self.logger.addHandler(self.handler)
        self.logger.setLevel(self.logging_level)

    def getLogger(self):
        return self.logger


if __name__ == "__main__":

    myAPIHelper = GeodesignHub.GeodesignHubClient(
        url=config.apisettings["serviceurl"],
        project_id=config.apisettings["projectid"],
        token=config.apisettings["apitoken"],
    )

    myLogger = ScriptLogger()
    logger = myLogger.getLogger()
    session = requests.Session()
    headers = {"Authorization": "Token " + config.apisettings["apitoken"]}
    session.headers = headers
    logger.info("Starting job")

    submissions_to_upload = []

    logger.info("Downloading project systems")
    systems_response = myAPIHelper.get_all_systems()
    system_list = []
    system_options = []
    if systems_response.status_code == 200:
        systems_response_json = json.loads(systems_response.text)
        for system in systems_response_json:
            system_list.append(
                {
                    "system_id": system["id"],
                    "system_name": system["name"],
                }
            )
            system_options.append(system["name"])
    else:
        logger.error("Error in downloading systems: %s" % systems_response.text)

    funding_type_dict = {
        "budgeted": "b",
        "public": "pu",
        "private": "pr",
        "public-private": "pp",
        "other": "o",
        "unknown": "u",
    }

    project_or_policy_options = ["project", "policy", "DO NOT ADD"]

    funding_type_options = [
        "budgeted",
        "public",
        "private",
        "public-private",
        "other",
        "unknown",
    ]
    swe_files = []
    base_folder = config.apisettings["swe_diagram_folder"]
    for root, dirs, files in os.walk(base_folder):
        for f in files:
            if f.endswith(".json") or f.endswith(".geojson"):
                category = os.path.basename(root)
                title = os.path.splitext(f)[0]
                swe_files.append({"path": os.path.join(root, f), "title": title, "category": category})

    for current_result in swe_files:
        project_or_policy_or_skip, project_or_policy_or_skip_index = pick(
            project_or_policy_options,
            "Title: "
            + current_result["title"]
            + "\nCategory:"
            + current_result["category"],
        )

        if project_or_policy_or_skip_index != 2:
            funding_type, funding_type_index = pick(
                funding_type_options,
                "Title: "
                + current_result["title"]
                + "\nCategory:"
                + current_result["category"],
            )
            funding_type = funding_type_dict[funding_type]

            selected_system_name, selected_system_index = pick(
                system_options,
                "Title: "
                + current_result["title"]
                + "\nCategory: "
                + current_result["category"],
            )
            system_list_filtered = list(
                filter(lambda x: x["system_name"] == selected_system_name, system_list)
            )
            selected_system_id = system_list_filtered[0]["system_id"]
            diagram_description = current_result["title"].replace("_", " ")

            if len(diagram_description) > 50:
                diagram_description = diagram_description[:50] + ".."

            with open(current_result["path"]) as geojson_file:
                fc_to_upload = json.load(geojson_file)
            submissions_to_upload.append(
                {
                    "projectorpolicy": project_or_policy_or_skip,
                    "featuretype": "polygon",
                    "description": diagram_description,
                    "sysid": selected_system_id,
                    "geojson": fc_to_upload,
                    "funding_type": funding_type,
                }
            )

    for current_submission_to_upload in submissions_to_upload:
        if config.apisettings["dryrun"]:
            print(current_submission_to_upload)
        else:
            try:
                upload = myAPIHelper.post_as_diagram(
                    geoms=current_submission_to_upload["geojson"],
                    projectorpolicy=current_submission_to_upload["projectorpolicy"],
                    featuretype=current_submission_to_upload["featuretype"],
                    description=current_submission_to_upload["description"],
                    sysid=current_submission_to_upload["sysid"],
                    fundingtype=current_submission_to_upload["funding_type"],
                )
            except Exception as e:
                print("Error in upload :" % e)
                logging.error("Error in upload %s" % e)
            else:
                print(upload.json())
