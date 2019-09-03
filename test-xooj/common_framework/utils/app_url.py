from django.urls import reverse


def get_home_module_urls(context):
    try:
        exercise_url = reverse("practice_exercise:index")
    except:
        exercise_url = None

    context['x_exercise_url'] = exercise_url

    try:
        course_url = reverse("course:list")
    except:
        course_url = None

    context['x_course_url'] = course_url

    try:
        x_tools_url = reverse("x_tools:list")
    except:
        x_tools_url = None

    context['x_tools_url'] = x_tools_url

    try:
        x_vulns_url = reverse("x_vulns:vuln_list")
    except:
        x_vulns_url = None

    context['x_vulns_url'] = x_vulns_url

    try:
        x_jeopardy_url = reverse("event_jeopardy:contest_home", args=(0,))
    except:
        x_jeopardy_url = None
    context['x_jeopardy_url'] = x_jeopardy_url

    try:
        x_ad_url = reverse("event_attack_defense:contest_home", args=(0,))
    except:
        x_ad_url = None
    context['x_ad_url'] = x_ad_url


    try:
        x_trial_url = reverse("event_trial:contest_home", args=(0,))
    except:
        x_trial_url = None
    context['x_trial_url'] = x_trial_url

    try:
        x_infiltration_url = reverse("event_infiltration:contest_home", args=(0,))
    except:
        x_infiltration_url = None
    context['x_infiltration_url'] = x_infiltration_url

    return context