from transformers import MarianMTModel, MarianTokenizer
model_name = "Helsinki-NLP/opus-mt-en-fr"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

def translate_text_to_french(text):
    inputs = tokenizer.encode(text, return_tensors="pt", padding=True, truncation=True)
    outputs = model.generate(inputs)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# print(translate_text_to_french("Cambodia"))
