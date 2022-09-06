from django import template
from django.utils.timezone import now

register = template.Library()


@register.simple_tag
def can_team_submit(puzzle, team):
    return puzzle.can_team_submit(team)


@register.simple_tag
def get_team_timeout(puzzle, team):
    return puzzle.team_timeout(team) + now()


@register.simple_tag
def get_hint_available_time(hint, team):
    return hint.time_when_will_be_unlocked(team)


@register.simple_tag
def all_prerequisites_met(hint, team):
    return hint.all_prerequisites_met(team)


@register.simple_tag
def can_team_take_hint(hint, team):
    return hint.can_team_take(team)


@register.simple_tag
def can_team_see_puzzle(puzzle, team):
    return puzzle.can_team_see(team)
