import streamlit as st
import os
import csv
from copy import deepcopy
import io
import base64

try:
    from fixedwidth import FixedWidth
except ImportError:
    from fixedwidth.fixedwidth import FixedWidth


def clean_row(row):
    # converts from OrderedDict to dict
    # removes leading and trailing spaces from values so it can be formatted nicely
    row = dict(row)
    return {k: v.strip() for k, v in row.items() if isinstance(v, str)}


def parse_number(number):
    if not number:
        return ""
    number = int(float(number.replace(",", "")))
    return number


def create_config(rows):
    def column_config(column_data):
        alignments = {
            "L": "left",
            "R": "right",
        }
        column_name = column_data.get("Data Field Names")
        start_pos = parse_number(column_data.get("Start"))
        length = parse_number(column_data.get("Length"))
        end_pos = parse_number(column_data.get("End"))
        alignment = column_data.get("Justify")
        alignment = alignments[alignment] if alignment else ""
        column_type = "string"
        if not column_name:
            return None
        return {
            column_name: {
                "type": column_type,
                "start_pos": start_pos,
                "end_pos": end_pos,
                "length": length,
                "alignment": alignment,
                "padding": " ",
                "required": False,
            }
        }

    CONFIG = {}
    for row in rows:
        row = clean_row(row)
        if column_config(row):
            CONFIG.update(column_config(row))
    return CONFIG


def file_selector(folder_path="."):
    filenames = os.listdir(folder_path)
    selected_filename = st.selectbox("Select a file", filenames)
    return os.path.join(folder_path, selected_filename)


def read_csv_file(file):
    from io import StringIO

    stringio = StringIO(file.getvalue().decode("utf-8"))
    dict_reader = csv.DictReader(stringio)
    return dict_reader


def read_fw_file(file):
    from io import StringIO

    stringio = StringIO(file.getvalue().decode("utf-8"))
    return stringio


def get_binary_file_downloader_html(bin_file, file_label="File"):
    with open(bin_file, "rb") as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href


def write_csv(data):
    def get_fieldnames(data):
        return {k for d in data for k in d.keys()}

    fieldnames = get_fieldnames(data)
    with open("yourfile.csv", "w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def main():

    st.header("App for converting csv to fixed-width and other way around")
    st.sidebar.subheader("Upload config file [.csv]")
    st.sidebar.write("Config file should be same for both ways!")
    config_file_upload = st.sidebar.file_uploader("Choose a file")
    if config_file_upload is not None:
        selection = st.sidebar.selectbox(
            "What would you like to convert?", ("CSV->FixedWidth", "FixedWidth->CSV")
        )
        config_file = read_csv_file(config_file_upload)
        CONFIG = create_config(config_file)
        # Reads config for FixedWidth lib
        fw_config = deepcopy(CONFIG)
        fw_obj = FixedWidth(fw_config)

        if selection == 'CSV->FixedWidth':
            st.subheader("Upload CSV file")
        else:
            st.subheader("Upload FixedWidth file")
        data_file = st.file_uploader("Upload a data file")
        if data_file is not None:
            if selection == "CSV->FixedWidth":
                data = read_csv_file(data_file)
                lines = ""
                for i, row in enumerate(data):
                    row = clean_row(row)
                    fw_obj.update(**row)
                    fw_string = fw_obj.line
                    lines += fw_string
                f = open("yourfile.main", "w")
                f.write(lines)
                f.close()
                st.markdown(
                    get_binary_file_downloader_html("yourfile.main", "my_file.main"),
                    unsafe_allow_html=True,
                )
            else:
                rows = []
                data = read_fw_file(data_file)
                for i, row in enumerate(data):
                    fw_obj.line = row
                    values = fw_obj.data
                    rows.append(values)
                write_csv(rows)
                st.markdown(
                    get_binary_file_downloader_html("yourfile.csv", "my_file.csv"),
                    unsafe_allow_html=True,
                )


main()