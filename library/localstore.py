from pathlib import Path
import json
import os
import csv
import datetime
import library.nrpylogger as nrpy_logger
import library.utils as utils


logger = nrpy_logger.get_logger(os.path.basename(__file__))


def load_json_from_file(dir_name, json_file_name):
    file_json = {}
    json_dir = Path(dir_name)
    if json_dir.exists():
        json_file = json_dir / json_file_name
        if json_file.exists():
            file_json = json.loads(json_file.read_text())
    else:
        logger.error(dir_name + " does not exist.")
    return file_json


def load_csv_to_list_of_dicts(file_name):
    list_of_dicts = []
    with open(file_name, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            list_of_dicts.append(row)
    return list_of_dicts


def create_dirs(dir_path):
    logger.debug("Creating " + dir_path)
    if '/' in dir_path:
        dirs = dir_path.split('/')
        base_dir = Path(dirs[0])
        for i, sub_dir in enumerate(dirs):
            if i > 0:
                base_dir = base_dir / sub_dir
        storage_dir = base_dir
    else:
        storage_dir = Path(dir_path)
    storage_dir.mkdir(mode=0o777, parents=True, exist_ok=True)
    logger.debug("created " + str(storage_dir))
    return storage_dir


def create_storage_dirs(account_id, timestamp):
    logger.debug("Creating storage dirs")
    base_dir = Path("db")
    storage_dir = base_dir / account_id / "monitors" / timestamp
    storage_dir.mkdir(mode=0o777, parents=True, exist_ok=True)
    logger.debug("created " + str(storage_dir))
    return storage_dir


def save_json_to_file(entity_json, file_name):
    curr_dir = Path(".")
    to_file = curr_dir / file_name
    store_file = create_file(to_file)
    store_file.write_text(json.dumps(entity_json, indent=utils.DEFAULT_INDENT))


def create_file(file_name):
    if file_name.exists():
        logger.info("Removing existing file " + file_name.name)
        os.remove(file_name)
    file_name.touch()
    if file_name.exists():
        logger.info("Created " + file_name.name)
    else:
        logger.error("Could not create " + file_name.name)
    return file_name


def load_names(from_file):
    names = []
    with open(from_file) as input_names:
        for monitor_name in input_names:
            names.append(monitor_name.rstrip().lstrip())
    return names


# creates and returns a file in the output directory
def create_output_file(file_name):
    logger.debug("Creating output file")
    output_dir = Path("output")
    output_dir.mkdir(mode=0o777, exist_ok=True)
    monitor_names_file = output_dir / file_name
    return create_file(monitor_names_file)


def sanitize(name):
    illegal_characters = ['/', '?', '<', '>', '\\', ':', '*', '|']
    characters = list(name)
    for index, character in enumerate(characters):
        if characters[index] in illegal_characters:
            characters[index] = '~'
    name = ''.join(characters)
    return name


def save_json(dir_path, file_name, dictionary):
    dir_path.mkdir(mode=0o777, parents=True, exist_ok=True)
    logger.debug("created " + str(dir_path))
    json_file = dir_path / file_name
    create_file(json_file)
    json_file.write_text(json.dumps(dictionary, indent=utils.DEFAULT_INDENT))


def save_csv(name: str, csv_data: list):
    output_dir = Path(".")
    csv_data_file = output_dir / name
    create_file(csv_data_file)
    with open(str(csv_data_file), 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',',
                                   quotechar='"', quoting=csv.QUOTE_ALL)
        csv_writer.writerows(csv_line + [""] for csv_line in csv_data)


def save_dict_as_csv(name: str, csv_data: dict, header: list):
    output_dir = Path(".")
    csv_data_file = output_dir / name
    create_file(csv_data_file)
    with open(str(csv_data_file), 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_ALL)
        csv_writer.writerow(iter(header))
        #for key, value in header.items():
        #    csv_writer.writerow([key, value])
        for key, value in csv_data.items():
            if "," in key:
                items_list = key.split(",")
                items_list.append(value)
                csv_writer.writerow(items_list)
            else:
                csv_writer.writerow([key, value])


def save_list_of_dict_as_csv(list_of_dicts, file_name):
    if list_of_dicts:
        column_names = list_of_dicts[0].keys()
        with open(file_name, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, column_names)
            dict_writer.writeheader()
            dict_writer.writerows(list_of_dicts)

def convert_timestamps_to_dates(violation):
    opened_at_date = datetime.fromtimestamp(violation['opened_at']/1000)
    violation['opened_at'] = opened_at_date
    if 'closed_at' in violation:
        closed_at_date = datetime.fromtimestamp(violation['closed_at']/1000)
        violation['closed_at'] = closed_at_date
    return violation