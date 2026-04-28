# Implement the `generate_image` tool

Status: pending
Tags: `mcp`, `writing`, `gemini-flash-image`, `imagen`, `multimodal`
Depends on: #014
Blocks: #016

## Scope

Implement Gemini Flash Image (`gemini-2.5-flash-image`) generation as the third writing tool. After this task, calling `generate_image(working_dir)` reads `post.md`, asks a *text* Gemini call to distill a text-free abstract visual scene from the post, then asks Gemini Flash Image to render that scene anchored to the branding + character profiles, with media examples from the dataset acting as few-shot style references. The result is saved as `post_image.png` (1200×1200, square).

This task introduces **multimodal output** (`response_modalities=["IMAGE"]`) and **multimodal input** (reference images via `Part(inline_data=Blob(...))`).

### Files to create

- `implement_yourself/src/writing/app/image_handler.py`

### Files to modify

- `implement_yourself/src/writing/utils/llm.py` — add `call_gemini_image(...)`.
- `implement_yourself/src/writing/config/prompts.py` — add `PROMPT_IMAGE_SCENE` and `PROMPT_GENERATE_IMAGE`.
- `implement_yourself/src/writing/tools/generate_image_tool.py` — replace placeholder body.

### Public interfaces

`utils/llm.py`:

```python
async def call_gemini_image(
    prompt: str,
    output_path: Path,
    reference_images: list[Path] | None = None,
) -> Path: ...
```

- `config = types.GenerateContentConfig(response_modalities=["IMAGE"])`.
- Build `contents: list[types.Part]` — for each reference image path that exists, append `Part(inline_data=Blob(mime_type=<derived from suffix>, data=img_bytes))` (mime map: `.jpg/.jpeg→image/jpeg`, `.png→image/png`, `.gif→image/gif`, fallback `image/png`). Append the text prompt as the final `Part(text=prompt)`.
- Call `client.aio.models.generate_content(model=settings.image_model, contents=contents, config=config)`.
- Walk `response.candidates[0].content.parts`; the first part with `inline_data is not None` is the image. Use Pillow (`PIL.Image.open(io.BytesIO(part.inline_data.data))`) to decode, `resize((1200, 1200))`, `save(str(output_path))`.
- If no candidate or no inline image is found, raise `RuntimeError("Gemini returned no image content.")` or `"Gemini response contained no image data."`.

`app/image_handler.py`:

```python
async def _extract_visual_scene(post_content: str) -> str:
    """Distill a text-free abstract visual scene from the post."""

async def generate_post_image(
    post_content: str,
    profiles: Profiles,
    output_path: Path,
    reference_images: list[Path] | None = None,
) -> Path: ...
```

- `_extract_visual_scene` formats `PROMPT_IMAGE_SCENE.format(post=post_content)`, calls `call_gemini(prompt)` (default writer model — text), returns the response text. Logs the extracted scene.
- `generate_post_image` derives `scene = await _extract_visual_scene(post_content)`, formats `PROMPT_GENERATE_IMAGE.format(branding_profile=..., character_profile=..., scene=scene)`, calls `call_gemini_image(prompt, output_path, reference_images)`, returns the path.

### Tool flow (`tools/generate_image_tool.py`)

1. Validate `post.md` exists in `working_dir`. Otherwise raise `FileNotFoundError`.
2. Read `post.md` content.
3. `profiles = load_profiles()`.
4. `examples = load_examples()` — `reference_images = [ex.media_path for ex in examples.media_examples]`.
5. `output_path = working_path / IMAGE_FILE` (`post_image.png`).
6. `await generate_post_image(post_content, profiles, output_path, reference_images)`.
7. Return:
   ```python
   {
     "status": "success",
     "image_path": str(output_path.resolve()),
     "message": f"Generated LinkedIn post image saved to {IMAGE_FILE}",
   }
   ```

### Prompt shapes

`PROMPT_IMAGE_SCENE` — a single `{post}` placeholder. Asks for ONE abstract visual scene (no diagrams, no text, geometric metaphors only). Constrains to: black background, white/gray shapes, orange accent, square 1:1, single focal point, no readable letters/numbers/labels, no people/faces/UI. Returns 2-3 sentences with no preamble. List a few example metaphors (chaos-to-order, compression, erosion, simplicity) so the LLM has anchor patterns.

`PROMPT_GENERATE_IMAGE` — placeholders `{branding_profile}`, `{character_profile}`, `{scene}`. Says "Generate an illustration matching the style of the reference images provided." Includes `<branding_profile>` and `<character_profile>` XML tags. Then the scene to illustrate. Then absolute rules: no text, not a diagram, single unified scene, black background + white/gray shapes + orange accents only, 1:1 1200x1200, no people/faces/hands.

### Notes

- Image generation requires `pillow` — already in `pyproject.toml`. No new dependencies.
- Some Gemini models reject reference images for image generation. The implementation does NOT need to special-case missing model support — surface errors to the harness via the raised `RuntimeError`.
- `media_examples` is limited to entries whose `scope` includes `train_image_generator` (already enforced by `load_examples()` from #012). Empty list is fine — `call_gemini_image` simply omits the `inline_data` parts.
- Always resize to 1200×1200 even if Gemini returns a different size — this is the canonical LinkedIn dimension for square posts.

## Acceptance Criteria

- [ ] After running the writing test workflow with all three tools, `test_logic/post_image.png` exists, is a valid PNG, and is exactly 1200×1200.
- [ ] If `post.md` is missing, the tool raises `FileNotFoundError`.
- [ ] If Gemini returns no image content, the tool raises `RuntimeError` with the message containing the words "no image".
- [ ] `_extract_visual_scene` returns a 2–3 sentence scene description (string, non-empty). The implementer can spot-check by reading the log line.
- [ ] `make test-writing-workflow` reports `Status: success` for all three tools (or at most surfaces the image step's error gracefully — the test script already wraps the image step in a try/except for environments without Imagen access).
- [ ] `make format-check && make lint-check` pass.

## User Stories

### Story: Attendee generates an image from the post

1. After `generate_post` and `edit_post` complete, attendee invokes `generate_image(working_dir="test_logic")`.
2. The tool calls Gemini twice: one text call to distill a scene, one image call to render. Logs show "Extracted visual scene: ..." with the abstract description.
3. After ~10–30s, `test_logic/post_image.png` exists. Opening it shows a black-background composition with white/gray geometric shapes and orange accents — no text, no people.

### Story: Style references shape the output

1. The dataset's `train_image_generator` entries supply ~1–3 reference images (see `index.yaml` for the labels).
2. The generated image visibly matches that style (similar palette, similar abstract geometric language).

### Story: Tool fails clearly when post is missing

1. Attendee runs `generate_image` against an empty directory.
2. Tool raises `FileNotFoundError: post.md not found in <dir>. Run generate_post first.`
3. Test script in `make test-writing-workflow` catches the error and prints "Image generation failed (may require Imagen access): ...".

---

Blocked by: #014
