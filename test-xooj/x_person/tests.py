from django.test import TestCase, RequestFactory

# Create your tests here.

from rest_framework.test import APITestCase

from common_auth.models import User
from django.contrib.auth.models import Group
from django.contrib.auth.models import AnonymousUser
from practice import models as practice_models
from django.test import Client
from x_person.cms.views import user_list


# https://docs.djangoproject.com/en/1.11/topics/testing/tools/

class Test(APITestCase):
    def setUp(self):
        print 'setUp'
        user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            is_active=True,
            is_staff=True
        )
        user.set_password('test1234')
        user.save()
        Group.objects.create(
            name='user'
        )
        self.factory = RequestFactory()
        self.user = user
        self.client.force_authenticate(self.user)

    def test_login(self):
        print 'test_login'
        self.assertTrue(self.client.login(username='admin', password='test1234'))

    # def test_login_fail(self):
    #     print 3
    #     self.assertTrue(self.client.login(username='admin', password='test134'))
    #
    # def test_logout(self):
    #     print 4
    #     self.client.logout()

    def test_get_user(self):
        test_user = User.objects.create(
            username='testuser',
            email='1212@example.com',
            is_active=True,
            is_staff=False
        )
        test_user.set_password('xctfoj01')
        test_user.save()
        response = self.client.get('/admin/x_person/api/users/%s/' % (test_user.id))
        self.assertTrue(response.status_code == 200)

    def test_create_user(self):
        response = self.client.post('/admin/x_person/api/users/',
                                    {'username': 'test_create', 'email': '123@qq.com', 'password': 'xctfoj01',
                                     'first_name': 'shengt', 'student_id': '12121',
                                     'groups': [Group.objects.all().first().id]})
        self.assertTrue(response.status_code == 201)
        self.assertTrue(self.client.login(username='test_create', password='xctfoj01'))

    def test_create_template(self):
        test_user = User.objects.create(
            username='testuser',
            email='1212@example.com',
            is_active=True,
            is_staff=False
        )
        test_user.set_password('xctfoj01')
        test_user.save()

        response = self.client.get('/admin/x_person/user_list/%s/' % (test_user.id))
        # [[{'False': False, 'None': None, 'True': True}, {u'csrf_token': <SimpleLazyObject: u'yHy0qvMlJidQesaRuow0T6qUxSAkF0kLOtI4hnQE3M853Y9MpuQhlDaGhnGWUXEM'>, 'user': <SimpleLazyObject: <django.contrib.auth.models.AnonymousUser object at 0x7f06be8c82d0>>, 'perms': <django.contrib.auth.context_processors.PermWrapper object at 0x7f06bdef05d0>, 'DEFAULT_MESSAGE_LEVELS': {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'SUCCESS': 25, 'ERROR': 40}, 'messages': <django.contrib.messages.storage.fallback.FallbackStorage object at 0x7f06c20300d0>, u'request': <WSGIRequest: GET '/admin/x_person/user_list/85/'>}, {}, {'faculty_list': <QuerySet []>, 'product_type': 0, 'userinfo': {u'status': 1, u'major': None, u'address': None, u'group_name': u'\u5b66\u5458', u'is_staff': False, u'logo': None, u'team_name': None, u'classes_name': None, u'first_name': u'', u'student_id': None, u'id': 85, u'faculty_name': None, u'logo_url': None, u'email': u'1212@example.com', u'username': u'testuser', u'ID_number': None, u'is_active': True, u'major_name': None, u'groups': [], u'faculty': None, u'password': u'pbkdf2_sha256$30000$HZGBQKHGIy77$hehIyLGmnHHmjAfLFxki4U8DERp+UXFUyEjimiemEWc=', u'nickname': None, u'mobile': None, u'brief_introduction': None, u'classes': None, u'team': None}, u'LANGUAGE_CODE': 'zh-hans', 'major_list': <QuerySet []>, 'classes_list': <QuerySet []>, 'group_list': <QuerySet [<Group: user>]>, 'mode': 1}],
        # [{'False': False, 'None': None, 'True': True}, {u'csrf_token': <SimpleLazyObject: u'yHy0qvMlJidQesaRuow0T6qUxSAkF0kLOtI4hnQE3M853Y9MpuQhlDaGhnGWUXEM'>, 'user': <SimpleLazyObject: <django.contrib.auth.models.AnonymousUser object at 0x7f06be8c82d0>>, 'perms': <django.contrib.auth.context_processors.PermWrapper object at 0x7f06bdef05d0>, 'DEFAULT_MESSAGE_LEVELS': {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'SUCCESS': 25, 'ERROR': 40}, 'messages': <django.contrib.messages.storage.fallback.FallbackStorage object at 0x7f06c20300d0>, u'request': <WSGIRequest: GET '/admin/x_person/user_list/85/'>}, {}, {'faculty_list': <QuerySet []>, 'product_type': 0, 'userinfo': {u'status': 1, u'major': None, u'address': None, u'group_name': u'\u5b66\u5458', u'is_staff': False, u'logo': None, u'team_name': None, u'classes_name': None, u'first_name': u'', u'student_id': None, u'id': 85, u'faculty_name': None, u'logo_url': None, u'email': u'1212@example.com', u'username': u'testuser', u'ID_number': None, u'is_active': True, u'major_name': None, u'groups': [], u'faculty': None, u'password': u'pbkdf2_sha256$30000$HZGBQKHGIy77$hehIyLGmnHHmjAfLFxki4U8DERp+UXFUyEjimiemEWc=', u'nickname': None, u'mobile': None, u'brief_introduction': None, u'classes': None, u'team': None}, u'LANGUAGE_CODE': 'zh-hans', 'major_list': <QuerySet []>, 'classes_list': <QuerySet []>, 'group_list': <QuerySet [<Group: user>]>, 'mode': 1}],
        # [{'False': False, 'None': None, 'True': True}, {u'csrf_token': <SimpleLazyObject: u'yHy0qvMlJidQesaRuow0T6qUxSAkF0kLOtI4hnQE3M853Y9MpuQhlDaGhnGWUXEM'>, 'user': <SimpleLazyObject: <django.contrib.auth.models.AnonymousUser object at 0x7f06be8c82d0>>, 'perms': <django.contrib.auth.context_processors.PermWrapper object at 0x7f06bdef05d0>, 'DEFAULT_MESSAGE_LEVELS': {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'SUCCESS': 25, 'ERROR': 40}, 'messages': <django.contrib.messages.storage.fallback.FallbackStorage object at 0x7f06c20300d0>, u'request': <WSGIRequest: GET '/admin/x_person/user_list/85/'>}, {}, {'faculty_list': <QuerySet []>, 'product_type': 0, 'userinfo': {u'status': 1, u'major': None, u'address': None, u'group_name': u'\u5b66\u5458', u'is_staff': False, u'logo': None, u'team_name': None, u'classes_name': None, u'first_name': u'', u'student_id': None, u'id': 85, u'faculty_name': None, u'logo_url': None, u'email': u'1212@example.com', u'username': u'testuser', u'ID_number': None, u'is_active': True, u'major_name': None, u'groups': [], u'faculty': None, u'password': u'pbkdf2_sha256$30000$HZGBQKHGIy77$hehIyLGmnHHmjAfLFxki4U8DERp+UXFUyEjimiemEWc=', u'nickname': None, u'mobile': None, u'brief_introduction': None, u'classes': None, u'team': None}, u'LANGUAGE_CODE': 'zh-hans', 'major_list': <QuerySet []>, 'classes_list': <QuerySet []>, 'group_list': <QuerySet [<Group: user>]>, 'mode': 1}, {'block': <Block Node: modal. Contents: [<TextNode: u'\n    '>, <django.template.loader_tags.IncludeNode object at 0x7f06bdf64f90>, <TextNode: u'\n'>]>}, {}],
        # [{'False': False, 'None': None, 'True': True}, {u'csrf_token': <SimpleLazyObject: u'yHy0qvMlJidQesaRuow0T6qUxSAkF0kLOtI4hnQE3M853Y9MpuQhlDaGhnGWUXEM'>, 'user': <SimpleLazyObject: <django.contrib.auth.models.AnonymousUser object at 0x7f06be8c82d0>>, 'perms': <django.contrib.auth.context_processors.PermWrapper object at 0x7f06bdef05d0>, 'DEFAULT_MESSAGE_LEVELS': {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'SUCCESS': 25, 'ERROR': 40}, 'messages': <django.contrib.messages.storage.fallback.FallbackStorage object at 0x7f06c20300d0>, u'request': <WSGIRequest: GET '/admin/x_person/user_list/85/'>}, {}, {'faculty_list': <QuerySet []>, 'product_type': 0, 'userinfo': {u'status': 1, u'major': None, u'address': None, u'group_name': u'\u5b66\u5458', u'is_staff': False, u'logo': None, u'team_name': None, u'classes_name': None, u'first_name': u'', u'student_id': None, u'id': 85, u'faculty_name': None, u'logo_url': None, u'email': u'1212@example.com', u'username': u'testuser', u'ID_number': None, u'is_active': True, u'major_name': None, u'groups': [], u'faculty': None, u'password': u'pbkdf2_sha256$30000$HZGBQKHGIy77$hehIyLGmnHHmjAfLFxki4U8DERp+UXFUyEjimiemEWc=', u'nickname': None, u'mobile': None, u'brief_introduction': None, u'classes': None, u'team': None}, u'LANGUAGE_CODE': 'zh-hans', 'major_list': <QuerySet []>, 'classes_list': <QuerySet []>, 'group_list': <QuerySet [<Group: user>]>, 'mode': 1}, {}],
        # [{'False': False, 'None': None, 'True': True}, {u'csrf_token': <SimpleLazyObject: u'yHy0qvMlJidQesaRuow0T6qUxSAkF0kLOtI4hnQE3M853Y9MpuQhlDaGhnGWUXEM'>, 'user': <SimpleLazyObject: <django.contrib.auth.models.AnonymousUser object at 0x7f06be8c82d0>>, 'perms': <django.contrib.auth.context_processors.PermWrapper object at 0x7f06bdef05d0>, 'DEFAULT_MESSAGE_LEVELS': {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'SUCCESS': 25, 'ERROR': 40}, 'messages': <django.contrib.messages.storage.fallback.FallbackStorage object at 0x7f06c20300d0>, u'request': <WSGIRequest: GET '/admin/x_person/user_list/85/'>}, {}, {'faculty_list': <QuerySet []>, 'product_type': 0, 'userinfo': {u'status': 1, u'major': None, u'address': None, u'group_name': u'\u5b66\u5458', u'is_staff': False, u'logo': None, u'team_name': None, u'classes_name': None, u'first_name': u'', u'student_id': None, u'id': 85, u'faculty_name': None, u'logo_url': None, u'email': u'1212@example.com', u'username': u'testuser', u'ID_number': None, u'is_active': True, u'major_name': None, u'groups': [], u'faculty': None, u'password': u'pbkdf2_sha256$30000$HZGBQKHGIy77$hehIyLGmnHHmjAfLFxki4U8DERp+UXFUyEjimiemEWc=', u'nickname': None, u'mobile': None, u'brief_introduction': None, u'classes': None, u'team': None}, u'LANGUAGE_CODE': 'zh-hans', 'major_list': <QuerySet []>, 'classes_list': <QuerySet []>, 'group_list': <QuerySet [<Group: user>]>, 'mode': 1}, {}]]


        self.assertTrue(response.context[0]['userinfo']['status'] == 1)
        self.assertTrue(response.status_code == 200)
        for template in response.templates:
            print template.name

            # x_person/cms/user_detail.html
            # cms/iframe_layout.html
            # cms/crop_modal.html
            # cms/js_templates/bootstrap_table.html
            # cms/js_templates/html_element.html

    def tearDown(self):
        pass

    def test_details(self):
        test_user = User.objects.create(
            username='testuser',
            email='1212@example.com',
            is_active=True,
            is_staff=False
        )
        test_user.set_password('xctfoj01')
        test_user.save()

        # Create an instance of a GET request.
        request = self.factory.get('/admin/x_person/user_list/%s/' % (test_user.id))

        # Recall that middleware are not supported. You can simulate a
        # logged-in user by setting request.user manually.
        request.user = self.user

        # Or you can simulate an anonymous user by setting request.user to
        # an AnonymousUser instance.
        # request.user = AnonymousUser()

        # Test my_view() as if it were deployed at /customer/details
        response = user_list(request)
        # Use this syntax for class-based views.
        # response = MyView.as_view()(request)
        self.assertEqual(response.status_code, 200)
