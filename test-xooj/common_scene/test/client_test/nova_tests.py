from __future__ import unicode_literals

from django.test import TestCase

from common_scene.clients import nova_client


class ComputeApiTests(TestCase):
    def setUp(self):
        super(ComputeApiTests, self).setUp()
        self.nv_cli = nova_client.Client()

    def tearDown(self):
        super(ComputeApiTests, self).tearDown()

    def test_get_servers(self):
        pass


