"""LLM settings of the pre-study (plan §14.14, D37-D40). Fixed for E3 and logged with every call.

Models (D37): Claude Haiku 5.5 writes and extracts; a writer subset (one draw per cell) uses Claude Sonnet 5.5,
with Claude Haiku 5.5 still as the extractor, the measuring instrument of the round trip. Thinking is off if the
pilot shows the output holds; otherwise it is adaptive with effort "low". Sampling is the API's default: current
models reject sampling parameters (D38). No fallback model (D39). The output is a JSON envelope carrying DSL
lines (D40).

Prices: USD per million tokens on the Claude API, from the price table of 6 Oct 2026 (Claude Haiku 5.5: prompts
up to 100K tokens). Cache reads as listed; cache writes cost 1.25 times the input price (5-minute TTL); the Batch
API halves every price. Replace the table when the prices change, and keep the date.

The LLM critic (D56, plan §14.29) is another vendor's model, so that it does not share the writer's and the
extractor's model family: OpenAI's GPT-6 Luna, priced like Claude Haiku 5.5, and GPT-6.1 Sol, priced like Claude
Sonnet 5.5, on a subset. Both reason before they answer, at the API's default effort, set explicitly; reasoning
tokens are billed as output. OpenAI prices from its price table of 20 Oct 2026 (standard tier, synchronous calls).
"""

WRITER = "claude-haiku-5-5"
WRITER_SUBSET = "claude-sonnet-5-5"
EXTRACTOR = "claude-haiku-5-5"
THINKING = "off"  # "off" or "adaptive" (D37)
EFFORT = "medium"  # the model's default, set explicitly; "low" if thinking has to be on (D37)
MAX_TOKENS = 16_000
CRITIC = "openai/gpt-6-luna"
CRITIC_STRONG = "openai/gpt-6.1-sol"
CRITIC_EFFORT = "medium"  # OpenAI's reasoning_effort; the API's default, set explicitly
CRITIC_MAX_TOKENS = 8_000  # reasoning and answer together; a critique that hits it is truncated, not parsed

PRICE_DATE = "2026-10-06"
PRICES = {  # input, output, cache read
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
    "claude-sonnet-5-5": (2.00, 10.00, 0.20),
    "claude-opus-5-5": (4.00, 20.00, 0.20),
    "openai/gpt-6-luna": (0.10, 0.50, 0.01),
    "openai/gpt-6.1-sol": (2.00, 10.00, 0.10),
}
PRICE_DATES = {"openai/gpt-6-luna": "2026-10-20", "openai/gpt-6.1-sol": "2026-10-20"}  # models priced on another day than PRICE_DATE
CACHE_WRITE = 1.25
BATCH_DISCOUNT = 0.5
