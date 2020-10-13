"""
    Methods for talking to the Kubernetes API server.

    All methods are expected to raise exceptions on problems, so that the
    caller can take care of the problem by itself.
"""

from django.conf import settings
from kubernetes import client
from kubeportal.k8s.utils import is_minikube
from base64 import b64decode
from kubeportal.k8s.utils import load_config

import logging

logger = logging.getLogger('KubePortal')

HIDDEN_NAMESPACES = ['kube-system', 'kube-public']
core_v1, rbac_v1 = load_config()


def create_k8s_ns(name):
    """
    Creates a new namespace in Kubernetes.

    Returns the client API object for the created Kubernetes namespace.
    """
    logger.info(f"Creating Kubernetes namespace '{name}'")
    try:
        k8s_ns = client.V1Namespace(
            api_version="v1", kind="Namespace", metadata=client.V1ObjectMeta(name=name))
        core_v1.create_namespace(k8s_ns)
    except client.rest.ApiException as e:
        if e.status == 409:
            # Namespace does already exist, nothing to do.
            logger.warning(f"Tried to create already existing Kubernetes namespace {name}. "
                           "Skipping the creation and using the existing one.")
        else:
            # Unknown problem, escalate
            raise e
    return core_v1.read_namespace(name=name)


def delete_k8s_ns(name):
    """
    Deletes a namespace in Kubernetes, but only in local development mode.

    """
    if is_minikube():
        logger.warning(f"Deletion of Kubernetes namespace '{name}', not happening in production.")
        core_v1.delete_namespace(name)
    else:
        logger.error("K8S namespace deletion not allowed in production clusters")


def get_namespaces():
    """
    Returns the list of cluster namespaces.
    """
    return core_v1.list_namespace().items


def get_namespace(name):
    """
    Get a API client namespace object by its name.
    """
    logger.debug(f"Fetching namespace object for {name}")
    ns_list = core_v1.list_namespace(field_selector=f"metadata.name={name}")
    assert(len(ns_list.items) == 1)
    return ns_list.items[0]


def get_service_accounts():
    """
    Returns the list of service accounts in all namespaces.
    """
    return core_v1.list_service_account_for_all_namespaces().items


def get_pods():
    """
    Returns the list of pods in all namespaces.
    """
    return core_v1.list_pod_for_all_namespaces().items


def get_token(kubeportal_service_account):
    """
    Get secret token for a Kubernetes service account.
    This is needed for generating a kubectl config file.

    Parameters:
        kubeportal_service_account: A service account model object.
    """
    service_account = core_v1.read_namespaced_service_account(
        name=kubeportal_service_account.name,
        namespace=kubeportal_service_account.namespace.name)
    secret_name = service_account.secrets[0].name
    secret = core_v1.read_namespaced_secret(
        name=secret_name, namespace=kubeportal_service_account.namespace.name)
    encoded_token = secret.data['token']
    return b64decode(encoded_token).decode()


def get_apiserver():
    """
    Returns host name and port number for the Kubernetes API server.
    """
    if settings.API_SERVER_EXTERNAL is None:
        return core_v1.api_client.configuration.host
    else:
        return settings.API_SERVER_EXTERNAL


def get_kubernetes_version():
    """
    Returns the version of the installed Kubernetes software.
    """
    pods = core_v1.list_namespaced_pod("kube-system").items
    for pod in pods:
        for container in pod.spec.containers:
            if 'kube-proxy' in container.image:
                return container.image.split(":")[1]
    logger.error(f"Kubernetes version not identifiable, list of pods in 'kube-system': {pods}.")
    return None


def get_number_of_pods():
    """
    Returns number of pods currently running in the cluster.
    This may take a while.
    """
    return len(core_v1.list_pod_for_all_namespaces().items)


def get_number_of_nodes():
    """
    Returns number of nodes currently running in the cluster.
    """
    return len(core_v1.list_node().items)


def get_number_of_cpu_cores():
    """
    Returns number of CPU cores currently installed in the cluster.
    """
    nodes = core_v1.list_node().items
    return sum([int(node.status.capacity['cpu']) for node in nodes])


def get_memory_sum():
    """
    Returns amount of main memory currently installed in the cluster, in GiBytes.
    """
    nodes = core_v1.list_node().items
    mems = [int(node.status.capacity['memory'][:-2]) for node in nodes]
    return sum(mems) / 1000000


def get_number_of_volumes():
    """
    Returns number of persistent volumes in the cluster, regardless of their provider.
    """
    return len(core_v1.list_persistent_volume().items)
