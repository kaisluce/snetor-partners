import pandas as pd
import time

from import_base_dataset import load_base_dataset

max_char = 35

def main():
    input_path = input_file_path()
    base_df = load_base_dataset(input_path)
    
    name_cols = chose_name_cols(base_df.columns.tolist())
    id_col = chose_id_col(base_df.columns.tolist())
    
    base_df["Name"] = (
        base_df[name_cols]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    
    length = chose_max_char()
    print(f"Max char for name columns set to: {length}")
    
    print(f"Do you want to process {len(base_df)} rows with the following name columns: {', '.join(name_cols)}? (y/n)")
    if input().strip().lower() != "y":
        print("Process cancelled by user.")
        time.sleep(2)
        return
    
    results = base_df.apply(reformate_names, axis=1)
    
    cols = results.columns.tolist()
    
    order = [id_col]
    order += sorted([col for col in cols if col.startswith("Name") and "updated" in col])
    order += sorted(name_cols)
    print(order)
    results = results[order]
    
    cols = results.columns.tolist()
    
    for col in cols[1:]:
        print(f"col: {col}, max : {max(results[col].fillna('').str.len())}")
    
    save_path = input_path[:-5] + "_update.xlsx"
    
    results.to_excel(save_path)
    print(f"Saved updated File as: {save_path}")


def reformate_names(row: pd.Series):
    global max_char
    name = row.get("Name", "")
    row["Name 1 updated"] = ""
    length = len(name)
    if length < max_char:
        row["Name 1 updated"] = name
        return row
    names = name.split(" ")
    part = 1
    for i in range(len(names)):
        n = names[i]
        if not row[f"Name {part} updated"] == "":
            row[f"Name {part} updated"] += " "
        len_with_name = len(row[f"Name {part} updated"]) + len(n)
        if len_with_name >= max_char - 1:
            max_len = max_char
            extra = len_with_name - max_len
            if len_with_name == max_char - 1 or len_with_name == max_char:
                if i == len(names) - 1:
                  row[f"Name {part} updated"] += n
                  break
                else:
                    extra = 1
            row[f"Name {part} updated"] += n[:-extra]
            part += 1
            if row.get(f"Name {part} updated") == None:
                got = row.get(f"Name {part} updated")
                row[f"Name {part} updated"] = ""
            row[f"Name {part} updated"] += n[-extra:]
        else:
            row[f"Name {part} updated"] += n
    return row
               
def input_file_path():
    path = ""
    print("Please enter the entry xlsx file path:\n")
    path = input()
    while not path.endswith(".xlsx"):
        print()
        print("Please make sure the entry file is an xlsx file.")
        print("Please enter the entry xlsx file path:")
        path = input()
    return path

def chose_name_cols(columns: list[str]) -> list[str]:
    applied_index_cols = [f"{i}: {col}" for i, col in enumerate(columns)]
    txt_columns = ",\n".join(applied_index_cols)
    print("Chose the columns with the partner name (separated by ','):")
    print(txt_columns)
    txt_choice = input()
    if txt_choice == "":
        print("Olease chose at least one column.")
        return chose_name_cols(columns)
    txt_choice = txt_choice.strip().replace(" ", "")
    try:
        index_list_choice = txt_choice.split(",")
        choices = [columns[int(i)] for i in index_list_choice]
    except:
        print("Please make sure the index is within the propositions.")
        return chose_name_cols(columns)
    return choices

def chose_id_col(columns: list[str]) -> str:
    applied_index_cols = [f"{i}: {col}" for i, col in enumerate(columns)]
    txt_columns = ",\n".join(applied_index_cols)
    print("Chose the ID column:")
    print(txt_columns)
    txt_choice = input().strip()
    if txt_choice == "":
        print("Please chose one column index.")
        return chose_id_col(columns)
    try:
        index_choice = int(txt_choice)
        if index_choice < 0 or index_choice >= len(columns):
            raise ValueError
    except:
        print("Please make sure the index is within the propositions.")
        return chose_id_col(columns)
    return columns[index_choice]

def chose_max_char():
    print("Please enter the max char for the name columns (default is 35):")
    global max_char
    txt_choice = input().strip()
    if txt_choice == "":
        return max_char
    try:
        int_choice = int(txt_choice)
        if int_choice <= 0:
            return max_char
        max_char = int_choice
        return max_char
    except:
        print("Please enter a valid positive integer.")
        return max_char
    
if __name__ == "__main__":
    main()
