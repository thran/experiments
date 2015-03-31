import os
import re
from proso.geography import answers as ga
import pandas as pd
import pylab as plt
import seaborn as sns
import numpy as np


def get_answers(from_csv=False, sample=False, min_answers_per_item=1000, min_answers_per_user=10):
    if from_csv or not os.path.exists("data/answers{}.pd".format(".sample" if sample else "")):
        answers = ga.from_csv("data/geography.answer{}.csv".format(".sample" if sample else ""))
        answers["correct"] = answers["place_asked"] == answers["place_answered"]
        answers = answers[answers.join(pd.Series(answers.groupby("place_asked").apply(len), name="count"), on="place_asked")["count"] > min_answers_per_item]
        answers = answers[answers.join(pd.Series(answers.groupby("user").apply(len), name="count"), on="user")["count"] > min_answers_per_user]
        answers["log_times"] = np.log(answers["response_time"] / 1000)
        answers = answers.join(np.exp(pd.Series(answers.groupby("user")["log_times"].apply(np.mean), name="user_mean")), on="user")
        answers = join_feedback(answers)
        answers = join_difficulties(answers)

        answers .to_pickle("data/answers{}.pd".format(".sample" if sample else ""))
    else:
        answers = pd.read_pickle("data/answers{}.pd".format(".sample" if sample else ""))

    return answers


def mark_class_room_users(answers, classroom_size=5):
    classroom_users = [
        user
        for ip, users in (
            answers.sort('id').drop_duplicates('user').
            groupby('ip_address').
            apply(lambda x: x['user'].unique()).
            to_dict().
            items())
        for user in users
        if len(users) > classroom_size
    ]
    answers["class"] = False
    answers.loc[answers["user"].isin(classroom_users), "class"] = True

def split_by_mean_time(answers, count=11, size=1, start=1):
    answers["speed"] = "longer"

    for bin in range(count):
        time = bin * size + start
        answers.loc[(time < answers["user_mean"]) & (answers["user_mean"] < (time + size)), "speed"] = "{}s-{}s".format(time, time + size)


def join_feedback(answers):
    feedback = pd.read_csv("data/feedback.rating.csv")
    answers = answers.join(pd.Series(feedback.groupby("user").apply(lambda x: x["value"].mean()), name="feedback"), on="user")
    return answers


def join_difficulties(answers):
    diffs = pd.read_csv("data/difficulties.csv").set_index("place")
    answers = answers.join(diffs, on="place_asked")
    return answers


def log_mean_time_hist(answers, classes=False):
    plt.title("Histogram of log-meanswers of response time of user")

    if classes:
        answers[~answers["class"]].groupby("user").first()["user_mean"].hist(bins=50, range=(0, 15), label="other")
        answers[answers["class"]].groupby("user").first()["user_mean"].hist(bins=50, range=(0, 15), label="in class")
        plt.legend(loc=1)
    else:
        answers.groupby("user").first()["user_mean"].hist(bins=50, range=(0, 15))
    # plt.xlim(0, 30)


def timesort(value):
    val = re.match("^(\d+)", value)
    val = int(val.group(0)) if val else 999
    return val


def compare_speed_and_accuracy(answers):
    speeds = sorted(answers["speed"].unique(), key=timesort)
    srs = []
    counts = []
    for speed in speeds:
        sr = answers[answers["speed"] == speed].groupby("user")["correct"].mean().mean()
        srs.append(sr)
        counts.append(len(answers.loc[answers["speed"] == speed]["user"].unique()))

    plt.figure()
    ax1 = plt.subplot()
    ax1.plot(range(len(speeds)), srs)
    plt.xticks(range(len(speeds)), speeds)
    ax1.set_xlabel("log-mean time")
    ax1.set_ylabel("avg success rate")
    ax2 = ax1.twinx()
    ax2.plot(range(len(speeds)), counts, "g")
    ax2.set_ylabel("user count")


def compare_speed_and_feedback(answers):
    speeds = sorted(answers["speed"].unique(), key=timesort)
    feedbacks = []
    counts = []
    for speed in speeds:
        feedback = answers[answers["speed"] == speed].groupby("user")["feedback"].mean().mean()
        feedbacks.append(feedback)
        counts.append(len(answers.loc[(answers["speed"] == speed) & pd.notnull(answers["feedback"])]["user"].unique()))

    plt.figure()
    ax1 = plt.subplot()
    ax1.plot(range(len(speeds)), feedbacks)
    plt.xticks(range(len(speeds)), speeds)
    ax1.set_xlabel("log-mean time")
    ax1.set_ylabel("avg of avg feedback")
    ax2 = ax1.twinx()
    ax2.plot(range(len(speeds)), counts, "g")
    ax2.set_ylabel("user count")


def compare_speed_and_difficulty(answers):
    speeds = sorted(answers["speed"].unique(), key=timesort)
    diffs = []
    counts = []
    for speed in speeds:
        diff = answers[answers["speed"] == speed].groupby("user")["difficulty"].mean().mean()
        diffs.append(diff)
        counts.append(len(answers.loc[(answers["speed"] == speed)]["user"].unique()))

    plt.figure()
    ax1 = plt.subplot()
    ax1.plot(range(len(speeds)), diffs)
    plt.xticks(range(len(speeds)), speeds)
    ax1.set_xlabel("log-mean time")
    ax1.set_ylabel("mean of avg difficulty")
    ax2 = ax1.twinx()
    ax2.plot(range(len(speeds)), counts, "g")
    ax2.set_ylabel("user count")


def compare_speed_and_class(answers):
    speeds = sorted(answers["speed"].unique(), key=timesort)
    class_rates = []
    counts = []
    for speed in speeds:
        class_rate = answers[answers["speed"] == speed]["class"].mean() * 100
        class_rates.append(class_rate)
        counts.append(len(answers.loc[(answers["speed"] == speed)]["user"].unique()))

    plt.figure()
    ax1 = plt.subplot()
    ax1.plot(range(len(speeds)), class_rates)
    plt.xticks(range(len(speeds)), speeds)
    ax1.set_xlabel("log-mean time")
    ax1.set_ylabel("% users from class")
    ax2 = ax1.twinx()
    ax2.plot(range(len(speeds)), counts, "g")
    ax2.set_ylabel("user count")


answers = get_answers(sample=False)

mark_class_room_users(answers)
split_by_mean_time(answers)
# compare_speed_and_accuracy(answers)
# compare_speed_and_feedback(answers)
# compare_speed_and_difficulty(answers)
# compare_speed_and_class(answers)


log_mean_time_hist(answers, classes=True)
plt.show()