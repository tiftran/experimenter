import json
import logging
import requests
from urllib.parse import urlparse, parse_qs

from django.conf import settings

INVALID_USER_ERROR_CODE = 51
INVALID_PARAMETER_ERROR_CODE = 53


class BugzillaError(Exception):
    pass


def format_bug_body(experiment):
    bug_body = ""

    if experiment.is_addon_experiment:
        variants_body = "\n".join(
            [
                experiment.BUGZILLA_VARIANT_ADDON_TEMPLATE.format(
                    variant=variant
                )
                for variant in experiment.variants.all()
            ]
        )
        bug_body = experiment.BUGZILLA_ADDON_TEMPLATE.format(
            experiment=experiment, variants=variants_body
        )
    elif experiment.is_pref_experiment:
        variants_body = "\n".join(
            [
                experiment.BUGZILLA_VARIANT_PREF_TEMPLATE.format(
                    variant=variant
                )
                for variant in experiment.variants.all()
            ]
        )
        bug_body = experiment.BUGZILLA_PREF_TEMPLATE.format(
            experiment=experiment, variants=variants_body,
        )

    return bug_body


def make_bugzilla_call(url, data):
    try:
        response = requests.post(url, data)
        return json.loads(response.content)
    except requests.exceptions.RequestException as e:
        logging.exception("Error calling Bugzilla API: {}".format(e))
        raise BugzillaError(*e.args)
    except json.JSONDecodeError as e:
        logging.exception("Error parsing JSON Bugzilla response: {}".format(e))
        raise BugzillaError(*e.args)


def format_creation_bug_body(experiment):
    bug_data = {
        "product": "Shield",
        "component": "Shield Study",
        "version": "unspecified",
        "summary": "[Experiment]: {experiment}".format(experiment=experiment),
        "description": experiment.BUGZILLA_OVERVIEW_TEMPLATE.format(
            experiment=experiment
        ),
        "assigned_to": experiment.owner.email,
        "cc": settings.BUGZILLA_CC_LIST,
        "type": "task",
        "priority": "P3",
        "see_also": [get_bugzilla_id(experiment.data_science_bugzilla_url)],
        "url": experiment.experiment_url,
        "whiteboard": experiment.STATUS_REVIEW_LABEL,
    }
    if experiment.firefox_version:
        cf_tracking = "cf_tracking_firefox{}".format(
            get_firefox_major_version(experiment.firefox_version)
        )
        bug_data[cf_tracking] = "?"

    if experiment.feature_bugzilla_url:
        bug_id = get_bugzilla_id(experiment.feature_bugzilla_url)
        bug_data["blocks"] = [bug_id]
    return bug_data


def create_experiment_bug(experiment):

    bug_data = format_creation_bug_body(experiment)
    response_data = make_bugzilla_call(settings.BUGZILLA_CREATE_URL, bug_data)

    # The experiment owner might not exist in bugzilla
    # in which case we try to create it again with no assignee
    if response_data.get("code", None) == INVALID_USER_ERROR_CODE:
        bug_data = bug_data.copy()
        del bug_data["assigned_to"]
        response_data = make_bugzilla_call(
            settings.BUGZILLA_CREATE_URL, bug_data
        )

    # Firefox Version given might not be an available
    # bugzilla tracking parameter, so remove and retry
    err_code = response_data.get("code", None) == INVALID_PARAMETER_ERROR_CODE
    if err_code:
        tracking_msg = "cf_tracking_firefox" in response_data.get(
            "message", None
        )
    if err_code and tracking_msg:
        bug_data = bug_data.copy()
        cf_tracking = "cf_tracking_firefox{}".format(
            get_firefox_major_version(experiment.firefox_version)
        )
        del bug_data[cf_tracking]
        response_data = make_bugzilla_call(
            settings.BUGZILLA_CREATE_URL, bug_data
        )

    if "id" not in response_data:
        raise BugzillaError(response_data["message"])
    return response_data["id"]


def get_firefox_major_version(version):
    return version.split(".")[0]


def get_bugzilla_id(bug_url):
    query = urlparse(bug_url).query
    return int(parse_qs(query)["id"][0])

def format_update_body(experiment):
    cf_tracking = "cf_tracking_firefox{}".format(
        get_firefox_major_version(experiment.firefox_version)
    )
    return {"summary": "[Experiment] {experiment_name} Fx {version} {channel}".format(experiment_name=experiment, version=experiment.firefox_version, channel= experiment.firefox_channel),
    "cf_user_story": format_bug_body(experiment),
    "whiteboard": experiment.STATUS_SHIP_LABEL,
    cf_tracking: "?"
    }

def update_experiment_bug(experiment):
    body=format_update_body(experiment)
    make_update_experiment_bug_call(settings.BUGZILLA_UPDATE_URL.format(id=experiment.bugzilla_id), body)

def make_update_experiment_bug_call(url, data):
    try:
        response = requests.put(url, data)
        return json.loads(response.content)
    except requests.exceptions.RequestException as e:
        logging.exception("Error calling Bugzilla API: {}".format(e))
        raise BugzillaError(*e.args)
    except json.JSONDecodeError as e:
        logging.exception("Error parsing JSON Bugzilla response: {}".format(e))
        raise BugzillaError(*e.args)

def add_experiment_comment(experiment):
    comment_data = {"comment": format_bug_body(experiment)}

    response_data = make_bugzilla_call(
        settings.BUGZILLA_COMMENT_URL.format(id=experiment.bugzilla_id),
        comment_data,
    )

    return response_data["id"]
