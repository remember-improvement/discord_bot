from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Load pretrained model and tokenizer
model_name = "gpt2"
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

# Fine-tuning (optional)
# Prepare your conversation dataset
train_data = [
    {"input": "Hello bot", "output": "Hello! How can I help you?"},
    {"input": "What's your name?", "output": "I am a chatbot."},
    # Add more training data here
]

# Tokenize and fine-tune (details below)
def generate_response(message):
    inputs = tokenizer.encode(message, return_tensors='pt')
    outputs = model.generate(inputs, max_length=20, num_return_sequences=1)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

# Example usage:
user_message = "What's your name?"
bot_response = generate_response(user_message)
print(bot_response)