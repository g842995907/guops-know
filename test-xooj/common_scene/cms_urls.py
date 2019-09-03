from django.conf.urls import include, url

from .cms import views

urlpatterns = [
    # url(r'^api/', include(router.urls, namespace='api')),
    url(r'^instance_api_list/$', views.instance_api_list, name='instance_api_list'),
    url(r'^image_api_list/$', views.image_api_list, name='image_api_list'),
    url(r'^network_api_list/$', views.network_api_list, name='network_api_list'),
    # url(r'^firewall_api_list/$', views.firewall_api_list, name='firewall_api_list'),

    url(r'^get_instance_list/$', views.get_instance_list, name='get_instance_list'),
    url(r'^delete_instance_by_id/$', views.delete_instance_by_id,
        name='delete_instance_by_id'),
    url(r'^delete_image_by_id/$', views.delete_image_by_id,
        name='delete_image_by_id'),
    url(r'^get_instance_detail_by_id/$', views.get_instance_detail_by_id,
        name='get_instance_detail_by_id'),
    url(r'^get_instance_list/$', views.get_instance_list, name='get_instance_list'),
    url(r'^get_image_list/$', views.get_image_list, name='get_image_list'),
    url(r'^get_image_detail_by_id/$', views.get_image_detail_by_id,
        name='get_image_detail_by_id'),
    url(r'^get_docker_server_list/$', views.get_docker_server_list, name='get_docker_server_list'),
    url(r'^delete_docker_by_id/$', views.delete_docker_by_id,
        name='delete_docker_by_id'),
    url(r'^get_docker_detail_by_id/$', views.get_docker_detail_by_id, name='get_docker_detail_by_id'),

    url(r'^get_network_list/$', views.get_network_list, name='get_network_list'),
    url(r'^delete_network_by_id/$', views.delete_network_by_id, name='delete_network_by_id'),
    url(r'^get_subnet_detail_by_id/$', views.get_subnet_detail_by_id,
        name='get_subnet_detail_by_id'),
    url(r'^get_router_list/$', views.get_router_list, name='get_router_list'),
    url(r'^get_router_detail_by_id/$', views.get_router_detail_by_id, name='get_router_detail_by_id'),
    url(r'^delete_router_by_id/$', views.delete_router_by_id, name='delete_router_by_id'),
    url(r'^get_float_ip_list/$', views.get_float_ip_list, name='get_float_ip_list'),
    url(r'^delete_floatip_by_id/$', views.delete_floatip_by_id, name='delete_floatip_by_id'),

    url(r'^get_fwaas_group_detail_by_id/$', views.get_fwaas_group_detail_by_id, name='get_fwaas_group_detail_by_id'),
    url(r'^get_fwaas_rules_list/$', views.get_fwaas_rules_list, name='get_fwaas_rules_list'),
    url(r'^get_fwaas_group_list/$', views.get_fwaas_group_list, name='get_fwaas_group_list'),
    url(r'^delete_fwaas_group_by_id/$', views.delete_fwaas_group_by_id, name='delete_fwaas_group_by_id'),
]



