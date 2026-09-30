# langgraph-reflexion-agent

An implementation of the Reflexion pattern in LangGraph: the model drafts an answer, critiques it, proposes search queries to fill the gaps, runs them, and revises with numbered citations. Unlike plain self-reflection, the critique here drives real web research, so each revision is grounded in sources rather than just reworded.

## What it does
- **`schemas.py`** — Pydantic models for the answer, the self-critique, and the search queries
- **`chains.py`** — one shared "expert researcher" prompt, specialised into a first-draft chain and a revision chain
- **`tool_executor.py`** — runs the model's proposed search queries against Tavily
- **`main.py`** — wires it into a `draft → execute_tools → revise` graph that loops back through search until the iteration cap

## Notes & details
- **Schemas as output formats, not real tools.** `AnswerQuestion` and `ReviseAnswer` are bound as tools with a forced `tool_choice`, so the model *must* respond by "calling" them. The result is guaranteed structure: answer, critique and search queries all come back together in one typed payload.
- **The neatest trick is in `tool_executor.py`.** The search function is registered with `ToolNode` under the names `AnswerQuestion` and `ReviseAnswer`. So when the model "calls" its answer schema, `ToolNode` intercepts that call and runs the search queries inside it. `**kwargs` quietly swallows the fields the search doesn't need, such as the answer and the critique.
- **Critique is split into `missing` and `superfluous`** — one pushes the next draft to add, the other pushes it to cut, which is what keeps revisions from just getting longer each round.
- **`ReviseAnswer` inherits from `AnswerQuestion`** and only adds `references`, so the revision step keeps the whole critique-and-search contract and bolts citations on top.
- **One prompt, two jobs.** `actor_prompt_template` is specialised with `.partial()`, so the draft and revision chains share the same persona and structure and differ only in their instructions.
- **Searches run concurrently** — `tavily_tool.batch(...)` fires all 1–3 proposed queries at once, at 5 results each.
- **The loop stops by counting `ToolMessage`s** against `MAX_ITERATIONS`, which puts a hard cap on search rounds regardless of whether the model thinks it's done.
- **The final answer lives in the tool call, not in `.content`.** The last message is an `AIMessage` whose answer and references sit inside `tool_calls[0]["args"]`, so print that if you want just the text.
- **`chains.py` runs standalone** — its `__main__` block pipes the first-draft chain through `PydanticToolsParser`, handy for tuning the draft prompt without running the whole graph.
- **The graph renders itself** to `mermaid.png` on every run.
- **Requires** `OPENAI_API_KEY` and `TAVILY_API_KEY` in `.env`.

## Run
```bash
uv sync
uv run main.py
```
