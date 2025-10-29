
### IMPORTS
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import pandas as pd
import os

### LOAD MODELS

# Translation model: Danish to English
translator = pipeline("translation", model="Helsinki-NLP/opus-mt-da-en", device='cpu')

# Language model: Qwen-3-4B
model_name = "Qwen/Qwen3-4B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="cpu"
)


### CHECK WHICH FILES TO PROCESS
processed_files = os.listdir('../data/csv/processed')
to_be_processed = []
for file in os.listdir('../data/csv/raw'):
    if file not in processed_files:
        to_be_processed.append(file)
to_be_processed


### APPLY PROCESSING
for file in to_be_processed:
    df_products = pd.read_csv(os.path.join('../data/csv/raw',file))
    
    # Add translated product names
    translation = translator(df_products['product_name'].values.tolist(), max_length=40)
    translation_list = [t['translation_text'] for t in translation]
    df_products['translated_product'] = translation_list
    print(translation_list)

    all_contents = []
    for index, row in df_products.iterrows():
        # prepare the model input
        prompt = f"Give me a fun/creative short single-sentence Tinder bio for me, but imagine I am the following grocery item: '{row['translated_product']}'. Only output the bio, and don't mention the word 'grocery'. Include 1 emoji."
        messages = [
            {"role": "user", "content": prompt}
        ]

        # Disable thinking mode
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False  # Disable thinking mode here
        )
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

        # conduct text completion
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=100
        )
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()

        # decode final output normally
        content = tokenizer.decode(output_ids, skip_special_tokens=True).strip("\n")
        print(row['translated_product'])
        print(content)
        print('----')
        all_contents.append(content)
    df_products['tinder_bio'] = all_contents

    df_products.to_csv(os.path.join('../data/csv/processed',file), index=False)