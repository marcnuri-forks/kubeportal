from django.contrib import messages
from kubernetes import client, config

import logging
logger = logging.getLogger('KubePortal')


def load_config():
    """
    Load Kubernetes credentials for the client library.
    Returns API objects for interaction.
    """
    try:
        # Production mode
        config.load_incluster_config()
        logger.debug("Loaded Kubernetes configuration in 'incluster' mode.")
    except Exception:
        # Dev mode
        config.load_kube_config()
        logger.debug("Loaded Kubernetes configuration in 'kubeconfig' mode.")
    return client.CoreV1Api(), client.RbacAuthorizationV1Api()


def is_minikube():
    """
    Checks if the current context is minikube. This is needed for checks in the test code.
    """
    contexts, active_context = config.list_kube_config_contexts()
    return active_context['context']['cluster'] == 'minikube'


def error_log(request, message):
    """
    Reports an error both to the frontend user and in the logs.
    """
    logger.error(message)
    messages.error(request, message)

