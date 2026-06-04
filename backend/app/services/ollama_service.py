import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger
from app.config import settings


class OllamaService:
    def __init__(self) -> None:
        self.base_url = str(settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.timeout = httpx.Timeout(120.0, connect=10.0)

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate(self, prompt: str) -> str:
        logger.info(
            "Sending prompt to Ollama | model={} prompt_length={}",
            self.model,
            len(prompt),
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 512
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                generated_text: str = data.get("response", "")

                logger.success(
                    "Ollama generation complete | model={} response_length={}",
                    self.model,
                    len(generated_text),
                )
                return generated_text

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Ollama HTTP error | status={} url={} detail={}",
                exc.response.status_code,
                exc.request.url,
                exc.response.text,
            )
            raise
        except httpx.TimeoutException as exc:
            logger.error("Ollama request timed out | url={}", exc.request.url if exc.request else self.base_url)
            raise
        except httpx.ConnectError as exc:
            logger.error("Ollama connection failed | base_url={} error={}", self.base_url, exc)
            raise
        except Exception as exc:
            logger.error("Unexpected error during Ollama generate | error={}", exc)
            raise

    async def health_check(self) -> bool:
        logger.info("Running Ollama health check | base_url={}", self.base_url)

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                is_healthy = response.status_code == 200
                if is_healthy:
                    logger.success("Ollama health check passed | base_url={}", self.base_url)
                else:
                    logger.warning(
                        "Ollama health check returned unexpected status | status={}",
                        response.status_code,
                    )
                return is_healthy

        except httpx.ConnectError as exc:
            logger.error("Ollama unreachable during health check | base_url={} error={}", self.base_url, exc)
            return False
        except httpx.TimeoutException:
            logger.error("Ollama health check timed out | base_url={}", self.base_url)
            return False
        except Exception as exc:
            logger.error("Unexpected error during Ollama health check | error={}", exc)
            return False


ollama_service = OllamaService()
