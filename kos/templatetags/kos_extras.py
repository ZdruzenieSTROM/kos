from django import template

register = template.Library()


@register.simple_tag
def get_hint_available_time(hint, team):
    return hint.time_when_will_be_unlocked(team)
