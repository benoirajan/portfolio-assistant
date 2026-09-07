# Gemini API Python Integration Guide (Gemini 2.5)

This repository provides standard integration patterns, setup guides, and code examples for using the official Google Gen AI Python SDK (`google-genai`) with **Gemini 2.5 Flash** and **Gemini 2.5 Pro**.

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [API Key Configuration](#api-key-configuration)
- [Project Setup](#project-setup)
- [Implementation Examples](#implementation-examples)
  - [1. Basic Text Generation](#1-basic-text-generation)
  - [2. Streaming Responses](#2-streaming-responses)
  - [3. Multi-turn Conversational Chat](#3-multi-turn-conversational-chat)
  - [4. System Instructions & Hyperparameters](#4-system-instructions--hyperparameters)
  - [5. Multimodal Input (Image + Text)](#5-multimodal-input-image--text)
  - [6. Structured JSON Output (Pydantic)](#6-structured-json-output-pydantic)
  - [7. Asynchronous Execution (AsyncIO / FastAPI)](#7-asynchronous-execution-asyncio--fastapi)
- [Model Selection Reference](#model-selection-reference)
- [Troubleshooting & Best Practices](#troubleshooting--best-practices)

---

## Prerequisites

- **Python:** Version 3.10 or higher recommended.
- **Google AI Studio Account:** An active API key from [Google AI Studio](https://aistudio.google.com/).

---

## Installation

Google's official, current Python SDK for the Gemini Developer API is `google-genai`:

```bash
pip install -U google-genai
```

*(Optional)* If you plan to process local images, install Pillow:

```bash
pip install -U pillow
```

*(Optional)* If you want optimized HTTP networking for asynchronous calls:

```bash
pip install -U "google-genai[aiohttp]"
```

---

## API Key Configuration

The SDK automatically resolves the API key from the `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) environment variable.

### Linux / macOS
```bash
export GEMINI_API_KEY="AIzaSyYourActualApiKeyHere"
```

### Windows (PowerShell)
```powershell
$env:GEMINI_API_KEY="AIzaSyYourActualApiKeyHere"
```

### Windows (Command Prompt)
```cmd
set GEMINI_API_KEY="AIzaSyYourActualApiKeyHere"
```

### Using `.env` (Recommended for Local Development)
Create a `.env` file in your root folder:
```env
GEMINI_API_KEY=AIzaSyYourActualApiKeyHere
```
Then load it in Python using `python-dotenv`:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Project Setup

A typical project structure looks like this:

```text
my-gemini-project/
├── .env
├── .gitignore
├── requirements.txt
├── main.py
└── README.md
```

**`requirements.txt`**:
```text
google-genai>=0.1.1
python-dotenv>=1.0.0
pydantic>=2.0.0
pillow>=10.0.0
```

---

## Implementation Examples

### 1. Basic Text Generation

Use `client.models.generate_content` for synchronous, single-turn prompts:

```python
import os
from google import genai

# Automatically detects GEMINI_API_KEY from environment
client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain microservices architecture in three concise bullet points.",
)

print(response.text)
```

---

### 2. Streaming Responses

For long outputs or low perceived latency in user-facing applications, stream chunks as they arrive:

```python
from google import genai

client = genai.Client()

response_stream = client.models.generate_content_stream(
    model="gemini-2.5-flash",
    contents="Write an essay outline detailing event-driven architecture.",
)

for chunk in response_stream:
    if chunk.text:
        print(chunk.text, end="", flush=True)
print()
```

---

### 3. Multi-turn Conversational Chat

The `chats` service manages conversation memory across turns:

```python
from google import genai

client = genai.Client()

# Create a stateful chat session
chat = client.chats.create(model="gemini-2.5-flash")

# First turn
response_1 = chat.send_message("I am building an enterprise REST API in Java Spring Boot.")
print("Model:", response_1.text)

# Second turn retains previous context
response_2 = chat.send_message("What database connection pooling library would you recommend for it?")
print("Model:", response_2.text)
```

---

### 4. System Instructions & Hyperparameters

Use `types.GenerateContentConfig` to pass runtime parameters such as temperature, token limits, and system personas:

```python
from google import genai
from google.genai import types

client = genai.Client()

config = types.GenerateContentConfig(
    system_instruction=(
        "You are an expert cloud infrastructure architect. "
        "Provide brief, strictly technical recommendations without conversational filler."
    ),
    temperature=0.2,
    max_output_tokens=500,
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What are the trade-offs between Amazon ECS Fargate and EKS for lightweight web APIs?",
    config=config,
)

print(response.text)
```

---

### 5. Multimodal Input (Image + Text)

Pass PIL Images, bytes, or file paths directly into the `contents` list:

```python
from google import genai
from PIL import Image

client = genai.Client()

# Open a local image
image = Image.open("architecture_diagram.png")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        image,
        "Analyze this system diagram and identify potential single points of failure.",
    ],
)

print(response.text)
```

---

### 6. Structured JSON Output (Pydantic)

To enforce clean, validated JSON schemas in API responses:

```python
from typing import List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class TechStackEvaluation(BaseModel):
    tool_name: str = Field(description="Name of the technology or framework")
    strengths: List[str] = Field(description="Core technical advantages")
    trade_offs: List[str] = Field(description="Potential bottlenecks or challenges")
    recommended_use_case: str = Field(description="Ideal scenario to deploy this tool")

client = genai.Client()

config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=TechStackEvaluation,
    temperature=0.1,
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Evaluate Apache Kafka for distributed event streaming.",
    config=config,
)

print(response.text)
```

---

### 7. Asynchronous Execution (AsyncIO / FastAPI)

Use `client.aio` for non-blocking asynchronous calls:

```python
import asyncio
from google import genai

async def main():
    # Asynchronous client context manager
    async with genai.Client() as client:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents="Summarize the purpose of circuit breaker patterns in distributed systems.",
        )
        print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Model Selection Reference

| Model Identifier | Primary Use Case | Context Window | Characteristics |
|---|---|---|---|
| `gemini-3.6-flash` | General reasoning, REST APIs, low-latency applications | 1,000,000 tokens | Balanced speed, high quality, free-tier friendly |
| `gemini-2.5-pro` | Complex algorithmic design, large codebase analysis | 1,000,000+ tokens | Maximum depth, enhanced reasoning |

---

## Troubleshooting & Best Practices

1. **API Key Not Found:**
   - Verify `echo $GEMINI_API_KEY` in your terminal.
   - If using `.env`, ensure `load_dotenv()` is called before `genai.Client()`.
2. **Handling Rate Limits (HTTP 429):**
   - In Google AI Studio free tier, enforce exponential backoff and jitter on retries.
   - For batch workloads, space out requests or switch from `gemini-2.5-pro` to `gemini-2.5-flash`.
3. **Session Resource Cleanup:**
   - When running batch workers or long-lived daemons, use context managers (`with genai.Client() as client:`) to ensure HTTP connections and sessions are cleanly released.