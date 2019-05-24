import markus
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from celery.utils.log import get_task_logger

from experimenter.celery import app
from experimenter.experiments import email, bugzilla, normandy
from experimenter.experiments.models import Experiment
from experimenter.notifications.models import Notification


logger = get_task_logger(__name__)
metrics = markus.get_metrics("experiments.tasks")


NOTIFICATION_MESSAGE_REVIEW_EMAIL = "An email was sent to {email} about {name}"
NOTIFICATION_MESSAGE_CREATE_BUG = (
    'A <a target="_blank" rel="noreferrer noopener" href="{bug_url}">Bugzilla '
    "Ticket</a> was created for your experiment"
)
NOTIFICATION_MESSAGE_CREATE_BUG_FAILED = (
    "Experimenter failed to create a Bugzilla Ticket "
    "for your experiment.  Please contact an Experimenter "
    "Administrator on #ask-experimenter on Slack."
)
NOTIFICATION_MESSAGE_ADD_COMMENT = (
    'The <a target="_blank" rel="noreferrer noopener" href="{bug_url}">'
    "Ticket</a> was updated with the details "
    "of this experiment"
)


@app.task
@metrics.timer_decorator("send_review_email.timing")
def send_review_email_task(
    user_id, experiment_name, experiment_url, needs_attention
):
    metrics.incr("send_review_email.started")
    logger.info("Sending email")

    email.send_review_email(experiment_name, experiment_url, needs_attention)
    logger.info("Email sent")

    Notification.objects.create(
        user_id=user_id,
        message=NOTIFICATION_MESSAGE_REVIEW_EMAIL.format(
            email=settings.EMAIL_REVIEW, name=experiment_name
        ),
    )
    metrics.incr("send_review_email.completed")


@app.task
@metrics.timer_decorator("create_experiment_bug.timing")
def create_experiment_bug_task(user_id, experiment_id):
    metrics.incr("create_experiment_bug.started")

    experiment = Experiment.objects.get(id=experiment_id)

    logger.info("Creating Bugzilla ticket")
    try:
        bugzilla_id = bugzilla.create_experiment_bug(experiment)
        logger.info("Bugzilla ticket created")
        experiment.bugzilla_id = bugzilla_id
        experiment.save()

        Notification.objects.create(
            user_id=user_id,
            message=NOTIFICATION_MESSAGE_CREATE_BUG.format(
                bug_url=experiment.bugzilla_url
            ),
        )
        metrics.incr("create_experiment_bug.completed")
        logger.info("Bugzilla ticket notification sent")
    except bugzilla.BugzillaError as e:
        metrics.incr("create_experiment_bug.failed")
        logger.info("Bugzilla ticket creation failed")

        Notification.objects.create(
            user_id=user_id, message=NOTIFICATION_MESSAGE_CREATE_BUG_FAILED
        )
        logger.info("Bugzilla ticket notification sent")
        raise e


@app.task
@metrics.timer_decorator("add_experiment_comment.timing")
def add_experiment_comment_task(user_id, experiment_id):
    metrics.incr("add_experiment_comment.started")

    experiment = Experiment.objects.get(id=experiment_id)

    if experiment.risk_internal_only:
        logger.info("Skipping Bugzilla comment for internal only experiment")
        return

    logger.info("Updating Bugzilla comment")

    try:
        bugzilla.add_experiment_comment(experiment)
        logger.info("Bugzilla comment updated")
        Notification.objects.create(
            user_id=user_id,
            message=NOTIFICATION_MESSAGE_ADD_COMMENT.format(
                bug_url=experiment.bugzilla_url
            ),
        )
        metrics.incr("add_experiment_comment.completed")
        logger.info("Bugzilla comment notification sent")
    except bugzilla.BugzillaError as e:
        metrics.incr("add_experiment_comment.failed")
        logger.info("Failed to create bugzilla comment")
        raise e


@app.task
@metrics.timer_decorator("update_experiment_status.timing")
def update_experiment_status():
    metrics.incr("update_experiment_status.started")
    accepted_experiments = Experiment.objects.filter(
        Q(status=Experiment.STATUS_ACCEPTED) | Q(status=Experiment.STATUS_LIVE)
    )
    status_mapping = update_mapping()
    for experiment in accepted_experiments:
        try:
            recipe_data = normandy.get_recipe(experiment.normandy_id)
            if needs_to_be_updated(recipe_data["enabled"], experiment.status):

                approver_email = recipe_data["approval_request"]["approver"][
                    "email"
                ]
                approver, _ = get_user_model().objects.get_or_create(
                    email=approver_email
                )

                experiment.status = status_mapping[experiment.status]
                experiment.save()

                experiment.changes.create(
                    changed_by=approver,
                    old_status=experiment.status,
                    new_status=status_mapping[experiment.status],
                )
                metrics.incr("update_experiment_status.updated")

        except (KeyError, normandy.NormandyError):
            logger.info(
                "Failed to get Normandy Recipe. Recipe ID: {}".format(
                    experiment.normandy_id
                )
            )
            metrics.incr("update_experiment_status.failed")
    metrics.incr("update_experiment_status.completed")


def needs_to_be_updated(enabled, status):
    accepted_update = enabled and status == Experiment.STATUS_ACCEPTED
    live_update = not enabled and status == Experiment.STATUS_COMPLETE
    return accepted_update or live_update


def update_mapping():
    return {
        Experiment.STATUS_ACCEPTED: Experiment.STATUS_LIVE,
        Experiment.STATUS_LIVE: Experiment.STATUS_COMPLETE,
    }
