import requests
import logging
from django.conf import settings
from django.contrib.auth import get_user_model


class NormandyError(Exception):
    pass


class NonsuccessfulNormandyCall(NormandyError):
    message = "Normandy API returned Nonsuccessful Response Code"


class APINormandyError(NormandyError):
    message = "Error calling Normandy API"


class NormandyDecodeError(NormandyError):
    message = "Error parsing JSON Normandy Response"


def make_normandy_call(url):
    try:
        response = requests.get(url, verify=False)
        print("printing response....")
        print(response)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.exception(
            "Normandy API returned Nonsuccessful Response Code: {}".format(e)
        )
        raise NonsuccessfulNormandyCall(*e.args)
    except requests.exceptions.RequestException as e:
        logging.exception("Error calling Normandy API: {}".format(e))
        raise APINormandyError(*e.args)
    except ValueError as e:
        logging.exception("Error parsing JSON Normandy response: {}".format(e))
        raise NormandyDecodeError(*e.args)


def get_recipe(recipe_id):
    recipe_url = settings.NORMANDY_API_RECIPE_URL.format(id=recipe_id)
    logging.info("PRINTING OMG PLEASE")
    logging.info(recipe_url)
    recipe_data = make_normandy_call(recipe_url)
    print(recipe_data)
    return recipe_data["approved_revision"]


def get_recipe_state_enabler(recipe_data):
    # set email default if no email/creator is found in normandy
    enabler_email = settings.NORMANDY_DEFAULT_CHANGELOG_USER

    enabled_states = recipe_data.get("enabled_states", [])
    if len(enabled_states) > 0:
        creator = enabled_states[0].get("creator")
        if creator:
            enabler_email = creator.get("email")

    enabler, _ = get_user_model().objects.get_or_create(
        email=enabler_email, username=enabler_email
    )
    return enabler
