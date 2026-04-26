from google import genai

client = genai.Client(api_key="AIzaSyBNMW9tBdq_ibiypvaBM_WUAbn2j_dYpqQ")

print("🔍 Listing available models for your account:")
print("-" * 40)

# In the 2026 SDK, it's 'supported_actions'
for model in client.models.list():
    if 'generateContent' in model.supported_actions:
        # We strip the 'models/' prefix to get the clean ID
        model_id = model.name.replace("models/", "")
        print(f"✅ {model_id}")

print("-" * 40)