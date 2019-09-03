#
#
# from rest_framework.test import APITestCase
#
# from common_auth.models import User
#
#
# class Test(APITestCase):
#     def setUp(self):
#         print 1
#         user = User.objects.create_user(
#             username='admin',
#             email='admin@example.com',
#             is_active=True,
#             is_staff=True
#         )
#         user.set_password('test1234')
#         user.save()
#
#     def test_login(self):
#         print 2
#         self.assertTrue(self.client.login(username='admin', password='test1234'))
#
#     def test_logout(self):
#         print 3
#         self.client.logout()
