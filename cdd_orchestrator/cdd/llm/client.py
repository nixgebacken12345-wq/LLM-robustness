from typing import Optional, Any
import instructor
from litellm import completion
from cdd.config import settings

# Patching litellm with instructor for production-grade structured output
client = instructor.patch(create=completion)

class LLMService:
    @staticmethod
    async def call_structured(
        prompt: str, 
        response_model: Any, 
        system_message: str = "You are a production-grade software architect.",
        model_override: Optional[str] = None
    ) -> Any:
        """
        Executes a structured LLM call with built-in retries and validation.
        """
        model = model_override or settings.DEFAULT_MODEL
        
        return client(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            response_model=response_model,
            max_retries=settings.RETRY_MAX_ATTEMPTS,
            api_key=settings.OPENAI_API_KEY.get_secret_value() if "gpt" in model else settings.ANTHROPIC_API_KEY.get_secret_value()
        )