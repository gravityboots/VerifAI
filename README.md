# VerifAI

### Our Problem Statement
The rapid spread of misinformation on social media and news platforms erodes digital trust, as people struggle to distinguish credible information from false claims. Manual fact-checking is too slow and ineffective for real-time contexts.

### The Proposed Solution
Our project develops an AI-driven fact-checker that extracts claims from online content, cross-checks them with trusted databases and fact-checking APIs, and provides users with real-time accuracy verification and explanations. This helps combat misinformation and empowers users to make informed decisions.

### How it works
- The project uses a RAG enhanced LLM to parse the user-selected text and generate a verdict of factuality/falsehood, summary and analysis.
- Tech stack of MistralAI for LLM sentence parsing, HuggingFace default model for vector embedding and ChromaDB for vector storage.
