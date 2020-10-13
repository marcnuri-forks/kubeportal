"""
Code to test the interaction methods for Kubernetes.
"""

from kubeportal.tests import AnonymousTestCase
from kubeportal.k8s import api


class Kubernetes(AnonymousTestCase):
    def test_get_namespace(self):
        ns_object = api.get_namespace("default")
        self.assertEqual("default", ns_object.metadata.name)

    def test_get_namespaces(self):
        ns_names = [item.metadata.name for item in api.get_namespaces()]
        self.assertIn("default", ns_names)
