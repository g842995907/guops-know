from cr_scene.models import CrEventScene, CrScene


def get_scene_by_id(scene_id, web=True):
    if scene_id is None:
        return None
    if web:
        cr_event = CrEventScene.objects.filter(cr_scene_instance=scene_id).first()
        if cr_event is None:
            cr_event = CrEventScene.objects.filter(id=scene_id).first()

        if cr_event:
            return CrScene.objects.filter(id=cr_event.cr_scene_id).first()
        else:
            return None
    else:
        cr_scene = CrScene.objects.filter(scene_id=scene_id).first()
        if cr_scene is None:
            cr_scene = CrScene.objects.filter(id=scene_id).first()

        return cr_scene


def get_cr_scene_by_id(cr_scene_id, cr_event_id):
    if cr_event_id:
        cr_event_scene = CrEventScene.objects.filter(id=cr_event_id).first()
        if cr_event_scene:
            return cr_event_scene.cr_scene
        return None

    return CrScene.objects.filter(id=cr_scene_id).first()
