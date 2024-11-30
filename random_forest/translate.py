import pandas as pd
from googletrans import Translator
import time

def translate_dataset(input_file, output_file, source_lang='en', target_lang='ru'):
    """
    Translates a dataset from source language to target language
    
    Parameters:
    input_file (str): Path to input CSV/text file
    output_file (str): Path to save translated output
    source_lang (str): Source language code (default: 'en')
    target_lang (str): Target language code (default: 'ru')
    """
    
    # Read the dataset
    try:
        df = pd.read_csv(input_file)
    except:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            df = pd.DataFrame(lines, columns=['text'])
    
    translator = Translator()
    translated_texts = []
    
    # Process in batches to avoid rate limits
    batch_size = 100
    
    for i in range(0, len(df), batch_size):
        batch = df['text'][i:i+batch_size]
        batch_translated = []
        
        for text in batch:
            try:
                translated = translator.translate(text, src=source_lang, dest=target_lang)
                batch_translated.append(translated.text)
            except Exception as e:
                print(f"Error translating text: {e}")
                batch_translated.append("")
            time.sleep(0.5)  # Delay to respect rate limits
            
        translated_texts.extend(batch_translated)
        print(f"Processed {min(i+batch_size, len(df))} out of {len(df)} lines")
    
    # Save translations
    df['translated_text'] = translated_texts
    df.to_csv(output_file, index=False)
    print(f"Translation completed. Output saved to {output_file}")