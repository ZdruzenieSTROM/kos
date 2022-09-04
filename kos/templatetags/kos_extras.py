from django import template

register = template.Library()


@register.simple_tag
def get_hint_available_time(hint, team):
    return hint.time_when_will_be_unlocked(team)


@register.simple_tag
def all_prerequisites_met(hint, team):
    return hint.all_prerequisites_met(team)


@register.simple_tag
def can_team_take_hint(hint, team):
    return hint.can_team_take(team)
