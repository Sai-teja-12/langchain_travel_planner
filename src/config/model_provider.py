import os
from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def create_model(temperature: float, provider: str = "gemini") -> BaseChatModel:
    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file")
        return ChatGoogleGenerativeAI(model=model_name, temperature=temperature, google_api_key=api_key)
    elif provider == "openai":
        # Lazy import for optional dependencies
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        return ChatOpenAI(model=model_name, temperature=temperature, openai_api_key=api_key)
    elif provider == "anthropic":
        # Lazy import for optional dependencies
        from langchain_anthropic import ChatAnthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in .env file")
        return ChatAnthropic(model=model_name, temperature=temperature, anthropic_api_key=api_key)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
