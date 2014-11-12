import json
from hashlib import sha1
import pandas as pd


def hash(model, data):
    return sha1(str(model)+str(data)).hexdigest()[:10]


def old_geography_data_parser(output, input="raw data/data-geography-first.csv"):
    with open(input) as fin, open(output, "w") as fout:
        fin.readline()

        for line in fin.readlines():
            line = line.split(",")
            qtype = int(line[4])
            answer = {
                "student": int(line[0]),
                "item": int(line[1]),
                "correct": line[3] == "1",
                "extra": {
                    "answer": int(line[2]),
                    "choices": 0 if qtype == 10 else (qtype - 10 * (qtype//10)),
                    "time": int(line[5]),
                },
            }
            fout.write(json.dumps(answer)+"\n")


def geography_data_parser(output, input="raw data/geography-all.csv"):
    data = pd.DataFrame.from_csv(input, index_col=False)
    data["correct"] = data["place_asked"] == data["place_answered"]
    data.rename(inplace=True, columns={
        "user": "student",
        "place_asked": "item",
        "place_answered": "answer",
        "response_time": "time",
        "number_of_options": "choices",
        "place_map": "map"
    })
    del data["options"]
    del data["inserted"]

    data["index"] = data["id"]
    data.set_index("index", inplace=True)
    data.save(output)


def filter_first(input="geography-all.pd", output=None):
    data = pd.load(input)

    filtered = data.groupby(["student"]). \
        apply(lambda x: x.drop_duplicates('item'))
    filtered["index"] = filtered["id"]
    filtered.set_index("index", inplace=True)

    filtered.save(output)
    print filtered


def filter_states(input="geography-first-all.pd", output=None):
    data = pd.load(input)

    filtered = data[data["type"] == 1]

    filtered.save(output)
    print filtered


def filter_europe(input="geography-first-all.pd", output=None):
    data = pd.load(input)

    filtered = data[data["item"].isin([51, 64, 66, 70, 74, 78, 79, 81, 88, 93, 94, 108, 113, 114, 115, 142, 143, 144, 146, 147, 154, 159, 164, 165, 176, 178, 179, 181, 182, 184, 190, 191, 194, 196, 203, 205, 206, 216, 234])]

    filtered.save(output)
    print filtered


def filter_cz_cities(input="geography-first-all.pd", output=None):
    data = pd.load(input)

    filtered = data[631 <= data["item"]]
    filtered = filtered[754 >= filtered["item"]]

    filtered.save(output)
    print filtered


def filter_small_data(input="geography-first-all.pd", output=None, min_students=200, min_items=20):
    data = pd.load(input)

    valid_users = map(
        lambda (u, n): u,
        filter(
            lambda (u, n): n >= min_items,
            data.groupby('student').apply(len).to_dict().items()
        )
    )
    data = data[data["student"].isin(valid_users)]

    valid_items = map(
        lambda (u, n): u,
        filter(
            lambda (u, n): n >= min_students,
            data.groupby('item').apply(len).to_dict().items()
        )
    )
    data = data[data["item"].isin(valid_items)]

    data.save(output)
    print data


# geography_data_parser("geography-all.pd")
# filter_first(output="geography-first-all.pd")
# filter_states(output="geography-first-states.pd")
# filter_europe(output="geography-first-europe.pd")
# filter_cz_cities(output="geography-first-cz_city.pd")
# filter_small_data(input="geography-first-europe.pd", output="geography-first-europe-filtered.pd", min_items=10)
# filter_small_data(input="geography-first-cz_city.pd", output="geography-first-cz_city-filtered.pd", min_items=10)