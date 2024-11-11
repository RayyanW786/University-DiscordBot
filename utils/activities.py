import random

from discord import Activity, ActivityType

__all__ = ["gen_activities", "gen_types"]


def gen_activities(bot, options: dict = None) -> Activity:
    """Generates and returns a random activity from the provided options"""
    if not options:
        options = {
            0: ["watch", f"{len(bot.users):,} Students"],
            1: ["watch", "Youtube"],
            2: ["listen", "Cyber Security Lectures"],
            3: ["watch", "Computer Science Lectures"],
            4: ["play", "Minecraft"],
        }

    activities = []
    for _, activity in options.items():
        activities.append(Activity(type=get_types(activity[0]), name=activity[1]))

    return random.choice(activities)


def get_types(activity_type: str) -> str:
    """Returns an activity type"""

    if activity_type == "watch":
        activity_type = ActivityType.watching
    elif activity_type == "play":
        activity_type = ActivityType.playing
    elif activity_type == "comp":
        activity_type = ActivityType.competing
    elif activity_type == "listen":
        activity_type = ActivityType.listening
    else:
        activity_type = ActivityType.custom

    return activity_type
