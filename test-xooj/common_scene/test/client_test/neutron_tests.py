from __future__ import unicode_literals

from django.test import TestCase

from common_scene.clients import neutron_client


class NetworkApiTests(TestCase):
    def setUp(self):
        super(NetworkApiTests, self).setUp()
        self.nt_cli = neutron_client.Client(
                 auth_url="http://controller:35357/v3/",
                 username="admin",
                 password="ADMIN_PASS", project_name="admin",
                 user_domain_id="default", project_domain_id="default")

    def tearDown(self):
        super(NetworkApiTests, self).tearDown()

    def test_qos_policy_create(self):
        pass


