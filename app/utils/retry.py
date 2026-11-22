from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import requests

# Example decorator for external API operations. Extend retryable exception types
# to match the provider SDK errors used in your installed versions.
retry_external = retry(
    wait=wait_exponential(multiplier=1, min=1, max=30),
    stop=stop_after_attempt(4),
    reraise=True,
)
