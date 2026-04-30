"""Binary LLM Judge metric for LinkedIn post evaluation."""

import logging
from typing import Any

from google import genai
from google.genai import types
from opik.evaluation.metrics import base_metric, score_result
from pydantic import BaseModel, Field

from writing.app.dataset_loader import DATASET_DIR, Label, load_by_scope
from writing.app.profile_loader import load_profiles
from writing.config.settings import get_settings

logger = logging.getLogger(__name__)

JUDGE_PROMPT = """
You are an expert LinkedIn content evaluator. Your job is to evaluate a generated
LinkedIn post against a set of writing profiles and the original guideline that
was used to produce it.

You do NOT have access to any ground truth post. Evaluate the generated post
based on the guideline intent, the research context, and the profile rules below.

**PROFILES — evaluate the generated post against these rules:**

<structure_profile>
{structure_profile}
</structure_profile>

<terminology_profile>
{terminology_profile}
</terminology_profile>

<character_profile>
{character_profile}
</character_profile>

**LABELING GUIDELINES:**

- LinkedIn writing is highly subjective. Leave room for creativity.
- Do NOT flag minor stylistic differences or word choice variations.
- Flag as "fail" ONLY for major violations:
  - Uses banned AI slop expressions or marketing terms from the terminology profile
  - Completely misses the core topic described in the guideline or research
  - Violates major structural rules (way too long, no hook, no CTA, uses markdown headers or excessive hashtags)
  - Sounds robotic/corporate/salesy when the character profile demands authentic voice
  - Fundamentally wrong tone (dismissive, condescending, preachy)
  - Uses passive voice throughout or wrong POV (e.g., refers to "one" instead of "you")
- If the generated post addresses the guideline's topic and follows the profiles
  reasonably well, label it "pass".

{few_shot_section}

**NOW EVALUATE THIS:**

<guideline>
{guideline}
</guideline>

<research_context>
{research}
</research_context>

<generated_post>
{generated_post}
</generated_post>

Return a JSON object with:
- "label": "pass" or "fail"
- "critique": 1-3 sentences explaining why. Be specific and concise.
""".strip()


class JudgeResult(BaseModel):
    """Structured output from the LLM judge."""

    label: str = Field(description="'pass' or 'fail'")
    critique: str = Field(description="1-3 sentence explanation")


class _FewShotExample(BaseModel):
    """A few-shot example for the judge (no ground truth)."""

    guideline: str
    generated_post: str
    label: str
    critique: str


def _build_few_shot_section(examples: list[_FewShotExample]) -> str:
    """Format few-shot examples for prompt injection.

    Args:
        examples: List of few-shot examples to include.

    Returns:
        Formatted string of examples, or empty string if no examples.
    """
    if not examples:
        return ""

    parts = ["**FEW-SHOT EXAMPLES — follow the same labeling logic:**"]
    for i, ex in enumerate(examples, 1):
        parts.append(
            f"""
<example_{i}>
<guideline>
{ex.guideline}
</guideline>
<generated_post>
{ex.generated_post}
</generated_post>
<expected_output>
label: {ex.label}
critique: {ex.critique}
</expected_output>
</example_{i}>"""
        )

    return "\n".join(parts)


class BinaryLLMJudgeMetric(base_metric.BaseMetric):
    """Binary pass/fail LLM judge for LinkedIn post evaluation.

    Evaluates a generated post against the guideline and writing profiles.
    No ground truth is used — the judge decides based on profile compliance
    and guideline adherence only.

    Few-shot examples are loaded from the train_evaluator split to align
    the judge with expert annotations.
    """

    def __init__(
        self,
        name: str = "binary_llm_judge",
        model: str | None = None,
    ) -> None:
        super().__init__(name=name)

        settings = get_settings()
        self._model = model or settings.reviewer_model
        self._client = genai.Client(api_key=settings.google_api_key.get_secret_value())

        # Load profiles from shipped markdown files
        profiles = load_profiles()
        self._structure_profile = profiles.structure.content
        self._terminology_profile = profiles.terminology.content
        self._character_profile = profiles.character.content

        # Load few-shot examples from train_evaluator
        few_shot_examples: list[_FewShotExample] = []
        train_entries = load_by_scope("train_evaluator")
        for entry in train_entries:
            if entry.label is None or entry.critique is None:
                continue
            generated = entry.generated_content(DATASET_DIR)
            guideline = entry.guideline_content(DATASET_DIR)
            if generated and guideline:
                few_shot_examples.append(
                    _FewShotExample(
                        guideline=guideline,
                        generated_post=generated,
                        label=entry.label.value,
                        critique=entry.critique,
                    )
                )

        self._few_shot_section = _build_few_shot_section(few_shot_examples)

    def _build_prompt(self, guideline: str, research: str, generated_post: str) -> str:
        """Build the full judge prompt.

        Args:
            guideline: The guideline used to produce the post.
            research: The research context (or empty string if none).
            generated_post: The generated LinkedIn post to evaluate.

        Returns:
            The formatted judge prompt string.
        """
        return JUDGE_PROMPT.format(
            structure_profile=self._structure_profile,
            terminology_profile=self._terminology_profile,
            character_profile=self._character_profile,
            few_shot_section=self._few_shot_section,
            guideline=guideline,
            research=research or "<none>",
            generated_post=generated_post,
        )

    def score(
        self,
        guideline: str,
        research: str,
        output: str,
        **ignored_kwargs: Any,
    ) -> score_result.ScoreResult:
        """Score a generated post against the guideline, research, and profiles.

        Args:
            guideline: The guideline that was used to generate the post.
            research: The research context used during generation.
            output: The generated LinkedIn post.
            **ignored_kwargs: Extra keyword arguments are ignored.

        Returns:
            ScoreResult with value 1.0 (pass) or 0.0 (fail) and reason.
        """
        prompt = self._build_prompt(guideline, research, output)

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=JudgeResult,
        )

        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=config,
        )

        result = JudgeResult.model_validate_json(response.text)

        return score_result.ScoreResult(
            name=self.name,
            value=1.0 if result.label == Label.PASS else 0.0,
            reason=f"[{result.label}] {result.critique}",
        )

    async def ascore(
        self,
        guideline: str,
        research: str,
        output: str,
        **ignored_kwargs: Any,
    ) -> score_result.ScoreResult:
        """Async version of score.

        Args:
            guideline: The guideline that was used to generate the post.
            research: The research context used during generation.
            output: The generated LinkedIn post.
            **ignored_kwargs: Extra keyword arguments are ignored.

        Returns:
            ScoreResult with value 1.0 (pass) or 0.0 (fail) and reason.
        """
        prompt = self._build_prompt(guideline, research, output)

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=JudgeResult,
        )

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=config,
        )

        result = JudgeResult.model_validate_json(response.text)

        return score_result.ScoreResult(
            name=self.name,
            value=1.0 if result.label == Label.PASS else 0.0,
            reason=f"[{result.label}] {result.critique}",
        )
