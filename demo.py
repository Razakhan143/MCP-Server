"""
  pip i bytez
"""

from bytez import Bytez

key = "427d4013cfeca5668bf2e91a815ee94b"
sdk = Bytez(key)

# choose tts-1-hd
model = sdk.model("openai/tts-1-hd")

# send input to model
results = model.run("Hello how are you doing today?")

print({ "error": results.error, "output": results.output })