# Migration from OpenAI to Groq - TODO

## Analysis
- Current setup uses OpenAI GPT-4 via langchain-openai
- Need to replace with Groq API
- Best model for code review: **llama-3.3-70b-versatile** (1K RPM, 500K TPM, good balance of performance and limits)

## Files to modify:
1. ✅ requirements.txt - Replace openai/langchain-openai with groq
2. ✅ config.py - Replace OPENAI_API_KEY with GROQ_API_KEY
3. ✅ analyzers/llm_analyzer.py - Replace ChatOpenAI with Groq client
4. ✅ .env.example - Update environment variable names
5. ✅ README.md - Update documentation

## Selected Model: llama-3.3-70b-versatile
- RPM: 1000 (vs OpenAI's typical 500)
- TPM: 500K tokens per minute
- Good for code analysis tasks
- Cost-effective alternative