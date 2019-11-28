import json

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from experimenter.experiments.constants import ExperimentConstants

from experimenter.experiments.models import Experiment
from experimenter.experiments.serializers import (
    ExperimentSerializer,
    ExperimentRecipeSerializer,
    ExperimentDesignPrefSerializer,
    ExperimentDesignMultiPrefSerializer,
    ExperimentDesignAddonSerializer,
    ExperimentDesignGenericSerializer,
)
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    ExperimentVariantFactory,
    VariantPreferencesFactory,
)


class TestExperimentListView(TestCase):

    def test_list_view_serializes_experiments(self):
        experiments = []

        for i in range(3):
            experiment = ExperimentFactory.create_with_variants()
            experiments.append(experiment)

        response = self.client.get(reverse("experiments-api-list"))
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)

        serialized_experiments = ExperimentSerializer(
            Experiment.objects.all(), many=True
        ).data

        self.assertEqual(serialized_experiments, json_data)

    def test_list_view_filters_by_status(self):
        pending_experiments = []

        # new experiments should be excluded
        for i in range(2):
            ExperimentFactory.create_with_variants()

        # pending experiments should be included
        for i in range(3):
            experiment = ExperimentFactory.create_with_variants()
            experiment.status = experiment.STATUS_REVIEW
            experiment.save()
            pending_experiments.append(experiment)

        response = self.client.get(
            reverse("experiments-api-list"), {"status": Experiment.STATUS_REVIEW}
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)

        serialized_experiments = ExperimentSerializer(
            Experiment.objects.filter(status=Experiment.STATUS_REVIEW), many=True
        ).data

        self.assertEqual(serialized_experiments, json_data)


class TestExperimentDetailView(TestCase):

    def test_get_experiment_returns_experiment_info(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_variants()

        response = self.client.get(
            reverse("experiments-api-detail", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        serialized_experiment = ExperimentSerializer(experiment).data
        self.assertEqual(serialized_experiment, json_data)


class TestExperimentRecipeView(TestCase):

    def test_get_experiment_recipe_returns_recipe_info(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_variants(
            normandy_slug="a-normandy-slug"
        )

        response = self.client.get(
            reverse("experiments-api-recipe", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        serialized_experiment = ExperimentRecipeSerializer(experiment).data
        self.assertEqual(serialized_experiment, json_data)


class TestExperimentSendIntentToShipEmailView(TestCase):

    def test_put_to_view_sends_email(self):
        user_email = "user@example.com"

        experiment = ExperimentFactory.create_with_variants(
            review_intent_to_ship=False, status=Experiment.STATUS_REVIEW
        )
        old_outbox_len = len(mail.outbox)

        response = self.client.put(
            reverse(
                "experiments-api-send-intent-to-ship-email",
                kwargs={"slug": experiment.slug},
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        experiment = Experiment.objects.get(pk=experiment.pk)
        self.assertEqual(experiment.review_intent_to_ship, True)
        self.assertEqual(len(mail.outbox), old_outbox_len + 1)

    def test_put_raises_409_if_email_already_sent(self):
        experiment = ExperimentFactory.create_with_variants(
            review_intent_to_ship=True, status=Experiment.STATUS_REVIEW
        )

        response = self.client.put(
            reverse(
                "experiments-api-send-intent-to-ship-email",
                kwargs={"slug": experiment.slug},
            ),
            **{settings.OPENIDC_EMAIL_HEADER: "user@example.com"},
        )

        self.assertEqual(response.status_code, 409)


class TestExperimentCloneView(TestCase):

    def test_patch_to_view_returns_clone_name_and_url(self):
        experiment = ExperimentFactory.create(
            name="great experiment", slug="great-experiment"
        )
        user_email = "user@example.com"

        data = json.dumps({"name": "best experiment"})

        response = self.client.patch(
            reverse("experiments-api-clone", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "best experiment")
        self.assertEqual(response.json()["clone_url"], "/experiments/best-experiment/")


class TestExperimentDesignPrefView(TestCase):

    def test_get_design_pref_returns_design_info(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_variants(type="pref")

        response = self.client.get(
            reverse("experiments-design-pref", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        serialized_experiment = ExperimentDesignPrefSerializer(experiment).data
        self.assertEqual(serialized_experiment, json_data)

    def test_put_to_view_saves_design_info(self):
        experiment = ExperimentFactory.create(
            name="great experiment", slug="great-experiment"
        )
        user_email = "user@example.com"

        variant_1 = {
            "name": "Terrific branch",
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
            "value": "value 1",
        }
        variant_2 = {
            "name": "Great branch",
            "ratio": 50,
            "description": "Very great branch.",
            "is_control": False,
            "value": "value 2",
        }

        data = json.dumps(
            {
                "type": "pref",
                "pref_key": "pref 1",
                "pref_branch": "default",
                "pref_type": "string",
                "variants": [variant_1, variant_2],
            }
        )

        response = self.client.put(
            reverse("experiments-design-pref", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

    def test_put_to_view_returns_400_on_missing_required_field(self):
        experiment = ExperimentFactory.create(
            name="great experiment", slug="great-experiment"
        )
        user_email = "user@example.com"

        variant_1 = {
            "name": "Terrific branch",
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
            "value": "value 1",
        }
        variant_2 = {
            "name": "Great branch",
            "ratio": 50,
            "description": "Very great branch.",
            "is_control": False,
            "value": "value 2",
        }

        data = json.dumps(
            {
                "type": "pref",
                "pref_branch": "default",
                "pref_type": "string",
                "variants": [variant_1, variant_2],
            }
        )

        response = self.client.put(
            reverse("experiments-design-pref", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["pref_key"], ["This field is required."])


class TestExperimentDesignMultiPrefView(TestCase):

    def setUp(self):
        self.user_email = "user@example.com"
        self.experiment = ExperimentFactory.create(type="pref")
        self.variant = ExperimentVariantFactory.create(
            experiment=self.experiment, is_control=True
        )
        self.preference = VariantPreferencesFactory.create(variant=self.variant)

    def test_get_design_multi_pref_returns_design_info(self):

        response = self.client.get(
            reverse(
                "experiments-design-multi-pref", kwargs={"slug": self.experiment.slug}
            ),
            **{settings.OPENIDC_EMAIL_HEADER: self.user_email},
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        serialized_experiment = ExperimentDesignMultiPrefSerializer(self.experiment).data
        self.assertEqual(serialized_experiment, json_data)

    def test_put_to_view_save_design_info(self):
        experiment = ExperimentFactory.create(
            name="an experiment", slug="an-experiment", type="pref"
        )
        variant = {
            "name": "variant1",
            "ratio": 100,
            "description": "variant1 description",
            "is_control": True,
            "preferences": [
                {
                    "pref_name": "the name is pref name",
                    "pref_value": "it's a string value",
                    "pref_type": "string",
                    "pref_branch": "default",
                }
            ],
        }
        data = json.dumps({"variants": [variant]})

        response = self.client.put(
            reverse("experiments-design-multi-pref", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: self.user_email},
        )

        self.assertEqual(response.status_code, 200)

    def test_put_to_view_returns_400_for_dup_pref_name(self):
        experiment = ExperimentFactory.create(
            name="an experiment", slug="an-experiment", type="pref"
        )
        variant = {
            "name": "variant1",
            "ratio": 100,
            "description": "variant1 description",
            "is_control": True,
            "preferences": [
                {
                    "pref_name": "the name is pref name",
                    "pref_value": "it's a string value",
                    "pref_type": "string",
                    "pref_branch": "default",
                },
                {
                    "pref_name": "the name is pref name",
                    "pref_value": "it's another string value",
                    "pref_type": "string",
                    "pref_branch": "default",
                },
            ],
        }
        data = json.dumps({"variants": [variant]})

        response = self.client.put(
            reverse("experiments-design-multi-pref", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: self.user_email},
        )

        self.assertEqual(response.status_code, 400)


class TestExperimentDesignAddonView(TestCase):

    def test_get_design_addon_returns_design_info(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_variants(
            type=ExperimentConstants.TYPE_ADDON
        )

        response = self.client.get(
            reverse("experiments-design-addon", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)

        serialized_experiment = ExperimentDesignAddonSerializer(experiment).data
        self.assertEqual(serialized_experiment, json_data)

    def test_put_to_view_saves_design_info(self):
        experiment = ExperimentFactory.create(
            name="great experiment",
            slug="great-experiment",
            type=ExperimentConstants.TYPE_ADDON,
        )
        user_email = "user@example.com"

        variant_1 = {
            "name": "Terrific branch",
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
        }
        variant_2 = {
            "name": "Great branch",
            "ratio": 50,
            "description": "Very great branch.",
            "is_control": False,
        }

        data = json.dumps(
            {
                "type": ExperimentConstants.TYPE_ADDON,
                "addon_experiment_id": "1234",
                "is_branched_addon": False,
                "addon_release_url": "http://www.example.com",
                "variants": [variant_1, variant_2],
            }
        )

        response = self.client.put(
            reverse("experiments-design-addon", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

    def test_put_to_view_returns_400_on_missing_required_field(self):
        experiment = ExperimentFactory.create(
            name="great experiment",
            slug="great-experiment",
            type=ExperimentConstants.TYPE_ADDON,
        )
        user_email = "user@example.com"

        variant_1 = {
            "name": "Terrific branch",
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
        }
        variant_2 = {
            "name": "Great branch",
            "ratio": 50,
            "description": "Very great branch.",
            "is_control": False,
        }

        data = json.dumps(
            {
                "type": ExperimentConstants.TYPE_ADDON,
                "addon_experiment_id": "1234",
                "variants": [variant_1, variant_2],
            }
        )

        response = self.client.put(
            reverse("experiments-design-addon", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["addon_release_url"], ["This field is required."]
        )


class TestExperimentDesignGenericView(TestCase):

    def test_get_design_addon_returns_design_info(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_variants(
            type=ExperimentConstants.TYPE_GENERIC
        )

        response = self.client.get(
            reverse("experiments-design-generic", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)

        serialized_experiment = ExperimentDesignGenericSerializer(experiment).data
        self.assertEqual(serialized_experiment, json_data)

    def test_put_to_view_saves_design_info(self):
        experiment = ExperimentFactory.create(
            name="great experiment",
            slug="great-experiment",
            type=ExperimentConstants.TYPE_GENERIC,
        )
        user_email = "user@example.com"

        variant_1 = {
            "name": "Terrific branch",
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
        }
        variant_2 = {
            "name": "Great branch",
            "ratio": 50,
            "description": "Very great branch.",
            "is_control": False,
        }

        data = json.dumps(
            {
                "type": ExperimentConstants.TYPE_GENERIC,
                "design": "design 1",
                "variants": [variant_1, variant_2],
            }
        )

        response = self.client.put(
            reverse("experiments-design-generic", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

    def test_put_to_view_design_is_optional(self):
        experiment = ExperimentFactory.create(
            name="great experiment",
            slug="great-experiment",
            type=ExperimentConstants.TYPE_GENERIC,
        )
        user_email = "user@example.com"

        variant_1 = {
            "name": "Terrific branch",
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
        }
        variant_2 = {
            "name": "Great branch",
            "ratio": 50,
            "description": "Very great branch.",
            "is_control": False,
        }

        data = json.dumps(
            {"type": ExperimentConstants.TYPE_GENERIC, "variants": [variant_1, variant_2]}
        )

        response = self.client.put(
            reverse("experiments-design-generic", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
