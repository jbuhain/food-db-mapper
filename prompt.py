import os
import pandas as pd
from openai import OpenAI

client = OpenAI()
client.api_key = os.getenv('OPENAI_API_KEY')

# Function to convert DataFrame to text
def df_to_text(df):
    rows = []
    for _, row in df.iterrows():
        food_name = row['FoodName']
        similar_foods = row['SIMILARFOODS']
        rows.append(f"FoodName: {food_name}\nSIMILARFOODS: {similar_foods}\nFILTEREDSIMILARFOODS: []\n")
    return '\n'.join(rows)

# Function to parse the GPT response text back to a DataFrame
def parse_input_text(input_text):
    data = {
        'FoodName': [],
        'SIMILARFOODS': [],
        'FILTEREDSIMILARFOODS': []
    }
    lines = input_text.strip().split('\n')
    for i in range(0, len(lines), 4):
        if i + 2 < len(lines):
            food_name_line = lines[i].split(': ', 1)
            similar_foods_line = lines[i+1].split(': ', 1)
            filtered_similar_foods_line = lines[i+2].split(': ', 1)

            if len(food_name_line) > 1 and len(similar_foods_line) > 1 and len(filtered_similar_foods_line) > 1:
                food_name = food_name_line[1]
                
                
                # Check if similar_foods_line[1] is NaN or empty
                if similar_foods_line[1].strip() and similar_foods_line[1] != 'nan' and similar_foods_line[1] != '':
                    try:
                        similar_foods = eval(similar_foods_line[1])
                    except SyntaxError:
                        similar_foods = set(similar_foods_line[1].strip('{}').split(', '))
                else:
                    similar_foods = ''
                
                # Check if filtered_similar_foods_line[1] is NaN or empty
                if filtered_similar_foods_line[1].strip() and filtered_similar_foods_line[1] != 'nan' and filtered_similar_foods_line[1] != '':
                    try:
                        filtered_similar_foods = eval(filtered_similar_foods_line[1])
                    except SyntaxError:
                        filtered_similar_foods = set(filtered_similar_foods_line[1].strip('{}').split(', '))
                else:
                    filtered_similar_foods = ''
                
                data['FoodName'].append(food_name)
                data['SIMILARFOODS'].append(similar_foods)
                data['FILTEREDSIMILARFOODS'].append(filtered_similar_foods)

    return pd.DataFrame(data)

def process_batch_OLD(df_batch):
    df_text = df_to_text(df_batch)
    PROMPT = ("Given the following set, could you fill in FILTEREDSIMILARFOODS by choosing the top food names inside SIMILARFOODS that correspond best to FoodName? Make sure that it matches the exact food names and not just related food name. Also, you do not have to choose any from the filtered similar food if you believe that none of the filtered foods matches the food name best. Make the output the same format as my input.")
    # print("-------------------")
    # print("INPUT", df_text)
    # print("-------------------")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": df_text},
        ],
        max_tokens=4096,
        temperature=0.2
    )

    result = response.choices[0].message.content
    # print("-------------------")
    # print("RESULT", result)
    # print("-------------------")
    # print()
    # print("------new batch--------")
    # print("-------------------")
    return parse_input_text(result)


def testAll_frida_to_nevo():
    # Process the DataFrame in batches of n rows
    # Adjust Starting and Final indexes for testing subset of data
    BATCH_SIZE = 10
    STARTING_INDEX = 775
    # FINAL_INDEX = len(sample_df)
    FINAL_INDEX = 885

    # Load results w/ SIMILARFOODS processed by langual similarity
    df_new = pd.read_excel('test_results/results_testAll_frida_to_nevo.xlsx')
    sample_df = df_new[['FoodName', 'SIMILARFOODS']]
    sample_df["FILTEREDSIMILARFOODS"] = '{}'

    batches = [sample_df.iloc[i:i + BATCH_SIZE] for i in range(STARTING_INDEX, FINAL_INDEX, BATCH_SIZE)]
    filtered_batches = []

    # Populate old values of filteredsimilarfoods
    results_df_old = pd.read_excel('test_results/GPT3.5_filtered_July17/results_part2_testAll_frida_to_nevo.xlsx')
    sample_df['FILTEREDSIMILARFOODS'] = results_df_old['FILTEREDSIMILARFOODS']

    for i, batch in enumerate(batches):
        filtered_batch = process_batch_OLD(batch)
        filtered_batches.append(filtered_batch)

        batch_index_start = STARTING_INDEX + (i * BATCH_SIZE)
        batch_index_end = batch_index_start + len(filtered_batch)
        print(f"batch {i} done. Index: {batch_index_start}-{batch_index_end}")
        
        # -1 since loc is inclusive.
        sample_df.loc[batch_index_start:batch_index_end-1, 'FILTEREDSIMILARFOODS'] = filtered_batch['FILTEREDSIMILARFOODS'].values
        
        # Save to excel
        sample_df.to_excel("test_results/GPT3.5_filtered_July17/results_part2_testAll_frida_to_nevo.xlsx", index=False)
        
        print(f"Batch {i} saved successfully.")

    # Display the final DataFrame
    print(sample_df)


def testAll_nevo_to_frida():
    # Process the DataFrame in batches of n rows
    # Adjust Starting and Final indexes for testing subset of data
    BATCH_SIZE = 10
    STARTING_INDEX = 0
    # FINAL_INDEX = len(sample_df)
    FINAL_INDEX = 100

    # Load results w/ SIMILARFOODS processed by langual similarity
    df_new = pd.read_excel('test_results/LangualSimilarity/results_LangualSimilarity_nevo_to_frida.xlsx')
    sample_df = df_new[['FoodName', 'SIMILARFOODS']]
    sample_df["FILTEREDSIMILARFOODS"] = '{}'

    batches = [sample_df.iloc[i:i + BATCH_SIZE] for i in range(STARTING_INDEX, FINAL_INDEX, BATCH_SIZE)]
    filtered_batches = []

    # Populate original values of filteredsimilarfoods
    results_df_old = pd.read_excel('test_results/GPT3.5_filtered_July17/results_GPT3.5Turbo_nevo_to_frida.xlsx')
    sample_df['FILTEREDSIMILARFOODS'] = results_df_old['FILTEREDSIMILARFOODS']

    for i, batch in enumerate(batches):
        filtered_batch = process_batch_OLD(batch)
        filtered_batches.append(filtered_batch)

        batch_index_start = STARTING_INDEX + (i * BATCH_SIZE)
        batch_index_end = batch_index_start + len(filtered_batch)
        print(f"batch {i} done. Index: {batch_index_start}-{batch_index_end}")
        
        # -1 since loc is inclusive.
        sample_df.loc[batch_index_start:batch_index_end-1, 'FILTEREDSIMILARFOODS'] = filtered_batch['FILTEREDSIMILARFOODS'].values
        
        # Save to excel
        sample_df.to_excel("test_results/GPT3.5_filtered_July17/results_part2_testAll_frida_to_nevo.xlsx", index=False)
        
        print(f"Batch {i} saved successfully.")

    # Display the final DataFrame
    print(sample_df)

if __name__ == "__main__":
    # testAll_frida_to_nevo()


