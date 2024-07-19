import pandas as pd
import os
import openpyxl
import ast


df_nevo_langal = pd.DataFrame()
df_frida_langal = pd.DataFrame()

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
        return set()  # or np.nan to output NaN instead of set()

def convert_to_set_from_preprocessed(string):
    try:
        return ast.literal_eval(string)
    except (ValueError, SyntaxError):
        return set()

def initialize_dataframes():
    global df_nevo_langal, df_frida_langal

    file_path = 'data/processed/preprocess/NL_RIVM-NEVO_2008-05-22.xlsx'
    df_nevo_langal = pd.read_excel(file_path)
    
    df_nevo_langal['LangualCodes'] = df_nevo_langal['LangualCodes'].apply(convert_to_set_from_preprocessed)

    # Excel file path
    file_path = 'data/processed/preprocess/Frida_preprocess_5.1_November_2023.xlsx'
    df_frida_langal = pd.read_excel(file_path)

    df_frida_langal['LangualCodes'] = df_frida_langal['LangualCodes'].apply(convert_to_set_from_preprocessed)

    df_frida_langal['SimilarFoods'] = ''
    df_nevo_langal['SimilarFoods'] = ''



def jaccard_similarity(set1, set2):
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(set1)

def get_highest_similarity_foodnames(df, foodname_column='FoodName'):
    max_score = df['SimilarityScore'].max()
    highest_similarity_rows = df[df['SimilarityScore'] == max_score]
    return set(highest_similarity_rows[foodname_column])

def get_highest_similarity_foodnames(df, foodname_column='FoodName'):
    max_score = df['SimilarityScore'].max()
    highest_similarity_rows = df[df['SimilarityScore'] == max_score]
    return set(highest_similarity_rows[foodname_column])

def get_row_by_engfdnam(engfdnam_value, origin_db):
    global df_nevo_langal, df_frida_langal
    
    if origin_db == 'nevo':
        return df_nevo_langal[df_nevo_langal['FoodName'] == engfdnam_value]
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
            print("Error: foodid_value must be an integer or a numeric string.")
            return
    
    if origin_db == 'nevo':
        return df_nevo_langal[df_nevo_langal['FoodID'] == foodid_value]
    elif origin_db == 'frida':
        return df_frida_langal[df_frida_langal['FoodID'] == foodid_value]
    else:
        raise ValueError("Invalid origin_db value. Use 'nevo' or 'frida'.")

# Main function to calculate similarities
# Bit messy, refactor this so that  column names are uniform!
def calculate_similarity(food_name, origin_db, target_db):
    global df_nevo_langal, df_frida_langal
    
    # determine origin DataFrame and select row based on food_name
    if origin_db == 'nevo':
        origin_df = df_nevo_langal
        origin_row = origin_df[origin_df['FoodName'] == food_name]
        if origin_row.empty:
            raise ValueError(f"No match found in {origin_db} database for food name: {food_name}")

        origin_set = origin_row['LangualCodes'].values[0]
    elif origin_db == 'frida':
        origin_df = df_frida_langal
        origin_row = origin_df[origin_df['FoodName'] == food_name]
        if origin_row.empty:
            raise ValueError(f"No match found in {origin_db} database for food name: {food_name}")

        origin_set = origin_row['LangualCodes'].values[0]
    else:
        raise ValueError("Invalid origin_db value. Use 'nevo' or 'frida'.")
    
    # determine target df
    if target_db == 'nevo':
        target_df = df_nevo_langal
    elif target_db == 'frida':
        target_df = df_frida_langal
    else:
        raise ValueError("Invalid target_db value. Use 'nevo' or 'frida'.")
    
    # calc similarity scores
    # Note: Similarity Scores will be deleted at the end
    
    if target_db == 'nevo':
        target_df['SimilarityScore'] = target_df['LangualCodes'].apply(lambda x: jaccard_similarity(origin_set, x))
    elif target_db == 'frida':
        target_df['SimilarityScore'] = target_df['LangualCodes'].apply(lambda x: jaccard_similarity(origin_set, x))

    # sort df based on SimilarityScore column from greatest to least
    temp_target_df = target_df.sort_values(by='SimilarityScore', ascending=False)

    # get food names w/ highest similarity score
    if target_db == 'nevo':
        highest_similarity_foodnames = get_highest_similarity_foodnames(temp_target_df, 'FoodName')
    elif target_db == 'frida':
        highest_similarity_foodnames = get_highest_similarity_foodnames(temp_target_df, 'FoodName')

    max_score = temp_target_df['SimilarityScore'].max()
    
    # print("max score", max_score)
    # format highest similarity food names w/ double quotes
    formatted_similarity_foodnames = {f'{name}' for name in highest_similarity_foodnames}
    # print(formatted_similarity_foodnames)
    # print("formatted_similarity_foodnames", formatted_similarity_foodnames)
    # print(food_name)
    # print([formatted_similarity_foodnames])
    # print(df_frida_langal.loc[df_frida_langal['FoodName'] == food_name])
    # update origin df w/ highest similarity food names

    if origin_db == 'nevo':
        for idx in df_nevo_langal.index[df_nevo_langal['FoodName'] == food_name]:
            df_nevo_langal.at[idx, 'SimilarFoods'] = formatted_similarity_foodnames
    elif origin_db == 'frida':
        for idx in df_frida_langal.index[df_frida_langal['FoodName'] == food_name]:
            df_frida_langal.at[idx, 'SimilarFoods'] = formatted_similarity_foodnames

    
    # update origin df w/ highest similarity food score
    if origin_db == 'nevo':
        df_nevo_langal.loc[df_nevo_langal['FoodName'] == food_name, 'SimilarityScore'] = max_score
        
    elif origin_db == 'frida':
        df_frida_langal.loc[df_frida_langal['FoodName'] == food_name, 'SimilarityScore'] = max_score
    
    # free up memory to make it faster? idk if this will help that much
    del temp_target_df
    return highest_similarity_foodnames
    
def founderrors():
    global df_nevo_langal, df_frida_langal
    count = 0
    initialize_dataframes()

    for index, row in df_nevo_langal.iterrows():
        if not row['FoodName']:
            count += 1
            print("Found an empty 'FoodName' at index:", index)
            print("Row details:", row)

    print("errors:",count)
    
def testAll_nevo_to_frida():
    initialize_dataframes()
    for index, row in df_nevo_langal.iterrows():
        if row['FoodName']:
            food_name = row['FoodName']
            try:
                calculate_similarity(food_name, 'nevo', 'frida')
            except Exception as e:
                print(f"Error processing {food_name}: {str(e)}")

    print(df_nevo_langal)
    df_nevo_langal.to_excel("test_results/LangualSimilarity/results_LangualSimilarity_nevo_to_frida.xlsx", index=False)

def testAll_frida_to_nevo():
    initialize_dataframes()
    for index, row in df_frida_langal.iterrows():
        if row['FoodName']:
            food_name = row['FoodName']
            try:
                calculate_similarity(food_name, 'frida', 'nevo')
            except Exception as e:
                print(f"Error processing {food_name}: {str(e)}")

    print(df_frida_langal)
    df_frida_langal.to_excel("test_results/LangualSimilarity/results_LangualSimilarity_frida_to_nevo.xlsx", index=False)

# %%
# Run initialization and similarity calculation
if __name__ == "__main__":
    testAll_nevo_to_frida()
    testAll_frida_to_nevo()

    # initialize_dataframes()

    ##########################################################
    # # Example usage of calculate_similarity function
    
    # # frida to nevo
    # result = calculate_similarity('Carrot, raw', 'frida', 'nevo')
    # print(result)
    # print(df_frida_langal)

    # # nevo to frida
    # result = calculate_similarity('Potatoes triangulardeep fat fried', 'nevo', 'frida')
    # print(result)
    # print(df_nevo_langal)

    # # # Example usage of get_row_by_engfdnam function
    # # row = get_row_by_engfdnam('Pineapple, canned', 'frida')
    # # print(row)
    
    ##########################################################
    # # Example usage of get_row_by_foodid function

    # row2 = get_row_by_foodid('4', 'frida')
    # print(row2)

