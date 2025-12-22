### IMPORTS
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import pandas as pd
import os
import gc
import torch

### CHECK WHICH FILES TO PROCESS
processed_files = os.listdir('../data/csv/processed')
to_be_processed = []
for file in os.listdir('../data/csv/raw'):
    if file not in processed_files:
        to_be_processed.append(file)
print(f"Files to process: {to_be_processed}")

### APPLY PROCESSING
for file in to_be_processed:
    print(f"\n=== Processing {file} ===")
    df_products = pd.read_csv(os.path.join('../data/csv/raw', file))
    
    # STEP 1: Load translation model, use it, then delete it
    print("Loading translation model...")
    translator = pipeline("translation", model="Helsinki-NLP/opus-mt-da-en", device='cpu')
    
    # Translate product names
    translation = translator(df_products['product_name'].values.tolist(), max_length=40)
    translation_list = [t['translation_text'] for t in translation]
    df_products['translated_product'] = translation_list
    print(f"Translated {len(translation_list)} products")
    
    # Clean up translation model
    del translator
    gc.collect()
    print("Translation model removed from memory")
    
    # STEP 2: Load Qwen model, use it, then delete it
    print("Loading Qwen model...")
    model_name = "Qwen/Qwen3-1.7B"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="cpu",
        low_cpu_mem_usage=True  # This helps reduce memory usage
    )
    
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
            enable_thinking=False
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
        
        # Clean up after each generation to prevent memory buildup
        del model_inputs, generated_ids, output_ids
        gc.collect()
    
    df_products['tinder_bio'] = all_contents

    # Save the processed file
    df_products.to_csv(os.path.join('../data/csv/processed', file), index=False)
    print(f"Saved processed file: {file}")
    
    # Clean up Qwen model before next file
    del model, tokenizer
    gc.collect()
    print("Qwen model removed from memory")

print("\n=== All files processed ===")