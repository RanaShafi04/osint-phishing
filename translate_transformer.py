from transformers import MarianMTModel, MarianTokenizer

model_lang = {
    'fr': 'Helsinki-NLP/opus-mt-en-fr',
    'ru': 'Helsinki-NLP/opus-mt-en-ru',
}
def get_translate_tokenizer_and_model(lang):
    tokenizer = MarianTokenizer.from_pretrained(model_lang[lang])
    model = MarianMTModel.from_pretrained(model_lang[lang])
    return tokenizer, model

def translate_text_to_target_lang(text, lang):
    tokenizer, model = get_translate_tokenizer_and_model(lang)
    inputs = tokenizer.encode(text, return_tensors="pt", padding=True, truncation=True)
    outputs = model.generate(inputs)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# print(translate_text_to_target_lang("Cambodia", 'ru'))
