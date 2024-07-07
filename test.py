# %%
import pandas as pd
import os
import openpyxl

# Global DataFrames
df_nevo_langal = pd.DataFrame()
df_frida_langal = pd.DataFrame()

# %%
def read_text_file(file_path):
    with open(file_path, 'r', encoding='latin-1') as file:
        lines = file.readlines()
    
    headers = lines[0].strip().split('\t')
    
    data = []
    for line in lines[1:]:
        fields = line.strip().split('\t')
        if len(fields) < len(headers):
            fields += [''] * (len(headers) - len(fields))
        data.append(fields)
    
    df = pd.DataFrame(data, columns=headers)
    return df

def read_excel_file(excel_path, sheet_name):
    xls = pd.ExcelFile(excel_path)
    df = pd.read_excel(xls, sheet_name)
    return df

def convert_to_set(langual_codes, delimiter=' '):
    if isinstance(langual_codes, str):
        return set(langual_codes.split(delimiter))
    else:
        return set()  # or np.nan if you prefer to keep NaN values

# %%
# Initialize DataFrames from files
def initialize_dataframes():
    global df_nevo_langal, df_frida_langal
    
    # Text file path
    text_file_path = 'data/NL RIVM-NEVO 2008-05-22.txt'
    df_nevo_langal = read_text_file(text_file_path)
    df_nevo_langal['LANGUALCODES'] = df_nevo_langal['LANGUALCODES'].apply(convert_to_set)

    # Excel file path
    excel_file_path = 'data/Frida_5.1_November_2023.xlsx'
    df_frida_langal = read_excel_file(excel_file_path, 'Food')
    df_frida_langal['LangualCode'] = df_frida_langal['LangualCode'].apply(lambda x: convert_to_set(x, delimiter=','))

# %%
# Define similarity functions
def jaccard_similarity(set1, set2):
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(set1)

def langual_similarity(code1, code2):
    set1 = set(code1.split())
    set2 = set(code2.split())
    return jaccard_similarity(set1, set2)

# %%
# Function to get rows with the highest similarity score
def get_highest_similarity_foodnames(df, foodname_column='ENGFDNAM'):
    max_score = df['SIMILARITYSCORE'].max()
    highest_similarity_rows = df[df['SIMILARITYSCORE'] == max_score]
    return set(highest_similarity_rows[foodname_column])

# %%
# Main function to calculate similarities
# Bit messy, refactor this so that the column names are uniform!
def calculate_similarity(food_name, origin_db, target_db):
    global df_nevo_langal, df_frida_langal
    
    # Determine the origin DataFrame and select the row based on food_name
    if origin_db == 'nevo':
        origin_df = df_nevo_langal
        origin_row = origin_df[origin_df['ENGFDNAM'] == food_name]
        if origin_row.empty:
            raise ValueError(f"No match found in {origin_db} database for food name: {food_name}")

        origin_set = origin_row['LANGUALCODES'].values[0]
    elif origin_db == 'frida':
        origin_df = df_frida_langal
        origin_row = origin_df[origin_df['FoodName'] == food_name]
        if origin_row.empty:
            raise ValueError(f"No match found in {origin_db} database for food name: {food_name}")

        origin_set = origin_row['LangualCode'].values[0]
    else:
        raise ValueError("Invalid origin_db value. Use 'nevo' or 'frida'.")
    
    # Determine the target DataFrame
    if target_db == 'nevo':
        target_df = df_nevo_langal
    elif target_db == 'frida':
        target_df = df_frida_langal
    else:
        raise ValueError("Invalid target_db value. Use 'nevo' or 'frida'.")
    
    # Calculate similarity scores
    if target_db == 'nevo':
        target_df['SIMILARITYSCORE'] = target_df['LANGUALCODES'].apply(lambda x: jaccard_similarity(origin_set, x))
    elif target_db == 'frida':
        target_df['SIMILARITYSCORE'] = target_df['LangualCode'].apply(lambda x: jaccard_similarity(origin_set, x))

    # Sort the DataFrame based on SIMILARITYSCORE column from greatest to least
    temp_target_df = target_df.sort_values(by='SIMILARITYSCORE', ascending=False)

    # Get food names with the highest similarity score
    if target_db == 'nevo':
        highest_similarity_foodnames = get_highest_similarity_foodnames(temp_target_df, 'ENGFDNAM')
    elif target_db == 'frida':
        highest_similarity_foodnames = get_highest_similarity_foodnames(temp_target_df, 'FoodName')
    

    # Format the highest similarity food names with double quotes
    formatted_similarity_foodnames = {f'"{name}"' for name in highest_similarity_foodnames}

    # Update the origin DataFrame with the highest similarity food names
    if origin_db == 'nevo':
        df_nevo_langal.loc[df_nevo_langal['ENGFDNAM'] == food_name, 'SIMILARFOODS'] = [formatted_similarity_foodnames]
    elif origin_db == 'frida':
        df_frida_langal.loc[df_frida_langal['FoodName'] == food_name, 'SIMILARFOODS'] = [formatted_similarity_foodnames]
    
    # free up memory to make it faster? idk if this will help that much
    del temp_target_df
    return highest_similarity_foodnames
    

# %%
# Function to get row by ENGFDNAM
def get_row_by_engfdnam(engfdnam_value, origin_db):
    global df_nevo_langal, df_frida_langal
    
    if origin_db == 'nevo':
        return df_nevo_langal[df_nevo_langal['ENGFDNAM'] == engfdnam_value]
    elif origin_db == 'frida':
        return df_frida_langal[df_frida_langal['FoodName'] == engfdnam_value]
    else:
        raise ValueError("Invalid origin_db value. Use 'nevo' or 'frida'.")

def get_row_by_foodid(foodid_value, origin_db):
    global df_nevo_langal, df_frida_langal

    if isinstance(foodid_value, str):
        try:
            foodid_value = int(foodid_value)
        except ValueError:
            # Handle the case where the string cannot be converted to an integer
            print("Error: foodid_value must be an integer or a numeric string.")
            return
    
    if origin_db == 'nevo':
        return df_nevo_langal[df_nevo_langal['FOODID'] == foodid_value]
    elif origin_db == 'frida':
        return df_frida_langal[df_frida_langal['FoodID'] == foodid_value]
    else:
        raise ValueError("Invalid origin_db value. Use 'nevo' or 'frida'.")

# %%
# Run the initialization and similarity calculation
if __name__ == "__main__":
    initialize_dataframes()
    
    # Example usage of calculate_similarity function
    
    # frida to nevo
    result = calculate_similarity('Strawberry, raw', 'frida', 'nevo')
    print(result)
    print(df_frida_langal)
    # nevo to frida
    result = calculate_similarity('Potatoes triangulardeep fat fried', 'nevo', 'frida')
    print(result)
    print(df_nevo_langal)
    # # Example usage of get_row_by_engfdnam function
    # row = get_row_by_engfdnam('Pineapple, canned', 'frida')
    # print(row)


    # # Example usage of get_row_by_foodid function
    # row2 = get_row_by_foodid('4', 'frida')
    # print(row2)
