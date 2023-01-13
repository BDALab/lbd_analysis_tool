import os
import pandas as pd


# Prepare the paths
temp_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'temp')
logs_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'logs')


def ensure_directory(path):
    dirs = os.path.dirname(path)
    if dirs and not os.path.exists(dirs):
        os.makedirs(dirs)
    if not os.path.exists(path):
        os.makedirs(path)


def save_to_excel(df, output_path, sheet_name="Sheet1", index=False):
    ensure_directory(output_path)
    with pd.ExcelWriter(output_path) as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=index)
        writer.save()


def save_to_excel_multi(dfs, sheet_names, output_path, index=False):
    ensure_directory(output_path)
    with pd.ExcelWriter(output_path) as writer:
        for df, sheet in zip(dfs, sheet_names):
            df.to_excel(writer, sheet_name=sheet, index=index)
            writer.save()


# Create the temporary directories
ensure_directory(temp_path)
ensure_directory(logs_path)
