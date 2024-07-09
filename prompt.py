import os
import pandas as pd
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()
client.api_key = os.getenv('OPENAI_API_KEY')

# Load your Excel file
df_new = pd.read_excel('test_results/results_testAll_frida_to_nevo.xlsx')
sample_df = df_new[['FoodName', 'SIMILARFOODS']]
sample_df["FILTEREDSIMILARFOODS"] = '{}'

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

# Function to process each batch with OpenAI API
def process_batch(df_batch):
    df_text = df_to_text(df_batch)
    PROMPT = ("Given the following set, could you fill in FILTEREDSIMILARFOODS by choosing the top food names inside SIMILARFOODS that correspond best to FoodName? Make sure that it matches the exact food names and not just related food name. Also, you do not have to choose any from the filtered similar food if you believe that none of the filtered foods matches the food name best. Make the output the same format as my input.")

    print("-------------------")
    print("INPUT", df_text)
    print("-------------------")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": df_text},
        ],
        max_tokens=4096
    )

    result = response.choices[0].message.content
    print("-------------------")
    print("RESULT", result)
    print("-------------------")
    print()
    print("------new batch--------")
    print("-------------------")
    return parse_input_text(result)

# Process the DataFrame in batches of 10 rows
batch_size = 10
# batches = [sample_df.iloc[i:i + batch_size] for i in range(0, len(sample_df), batch_size)]

batches = [sample_df.iloc[i:i + batch_size] for i in range(1140, 1200, batch_size)]
filtered_batches = []

for batch in batches:
    filtered_batch = process_batch(batch)
    filtered_batches.append(filtered_batch)
    print("batch done: ",filtered_batch)

# Concatenate all filtered batches into a single DataFrame
filtered_df = pd.concat(filtered_batches).reset_index(drop=True)
sample_df['FILTEREDSIMILARFOODS'] = filtered_df['FILTEREDSIMILARFOODS']

# Display the final DataFrame
print(sample_df)

sample_df.to_excel("test_results/process2/results_part2_testAll_frida_to_nevo.xlsx", index=False)
