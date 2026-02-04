# ELEVIX Chat Agent – Fool‑Proof LangChain Implementation (Agent‑First Design)

This document defines a **robust, production‑safe implementation** of the **ELEVIX chat agent**.

The focus here is **ONLY the agent logic**.

- Tools (**RAG tool**, **Web Search tool**) are assumed to exist
- Tool implementations are **explicitly excluded**
- This document defines **how and when the agent uses them**

ELEVIX behaves as a **conversational HR assistant** that:
- Engages naturally with users
- Uses **RAG strictly** for HR / Leave / Policy questions
- Uses **Web Search** only for general factual queries
- Refuses unsafe fallbacks
- Never hallucinates HR policies

---

## 1. Design Principles (Non‑Negotiable)

These rules are enforced at the **agent level**, not inside tools.

1. **Intent drives tool choice** – never the LLM’s whim
2. **HR queries NEVER use web search**
3. **Missing HR context = explicit refusal**
4. **General chat stays conversational**
5. **Agent never chains tools automatically**

If any rule breaks, the agent must **stop and respond safely**.

---

## 2. Agent Responsibilities

ELEVIX is responsible for:

- Maintaining conversation state
- Classifying user intent
- Selecting the correct tool (or none)
- Enforcing refusal rules
- Formatting user‑facing responses

ELEVIX is **not responsible for**:
- Fetching documents
- Searching the web
- Embedding or retrieval

Those are delegated to tools.

---

## 3. Supported User Intents

The agent recognizes **three high‑level intents**:

| Intent | Description | Tool Allowed |
|------|------------|-------------|
| HR_POLICY | Leave, HR rules, benefits, internal policies | RAG ONLY |
| GENERAL_FACT | Public facts, who‑is‑who, weather, dates | Web Search ONLY |
| SMALL_TALK | Greetings, acknowledgements, clarifications | No tools |

If intent is ambiguous → **clarify, do not guess**.

---

## 4. Tool Contracts (Assumed)

The agent assumes the following tool interfaces exist.

### 4.1 HR RAG Tool

```python
rag_tool.run(
    query: str,
    chat_history: list
) -> {
    "answer": str,
    "has_context": bool
}
```

Rules:
- `has_context=False` means documents were insufficient
- The agent MUST NOT override this

---

### 4.2 Web Search Tool

```python
web_search_tool.run(
    query: str
) -> str
```

Rules:
- Used only for **non‑HR factual queries**
- Never used as fallback for HR

---

## 5. System Prompt (Agent Identity)

```python
SYSTEM_PROMPT = """
You are ELEVIX, a conversational HR assistant.

Behavior Rules:
- Be polite, professional, and clear
- Engage naturally in conversation
- You decide WHICH tool to use, but only if allowed

Strict Rules:
- HR or Leave related questions MUST use the HR RAG tool
- HR questions MUST NEVER use web search
- If HR RAG tool reports insufficient context, respond with:
  "I couldn't find this information in the company documents."
- General factual questions MAY use web search
- Casual conversation should NOT use any tool
- Never hallucinate policies or rules
"""
```

This prompt is **non‑negotiable**.

---

## 6. Intent Classification (Agent‑Side)

Intent classification happens **before tool invocation**.

```python
def classify_intent(user_query: str) -> str:
    """
    Returns one of:
    - HR_POLICY
    - GENERAL_FACT
    - SMALL_TALK
    """
```

Classification signals:

### HR_POLICY
- leave, holiday, PTO, sick leave
- HR policy, benefits, payroll
- internal rules, approvals

### GENERAL_FACT
- who is / what is
- weather, location, date
- public company or person

### SMALL_TALK
- greetings
- thanks
- confirmations

If confidence < threshold → ask clarification.

---

## 7. Agent Decision Flow (Critical Section)

```text
User Query
   ↓
Intent Classification
   ↓
┌─────────────────────────────┐
│ HR_POLICY?                  │
│  → Use RAG Tool ONLY        │
│  → If has_context=False     │
│       → Refuse safely       │
└─────────────────────────────┘

┌─────────────────────────────┐
│ GENERAL_FACT?               │
│  → Use Web Search Tool      │
└─────────────────────────────┘

┌─────────────────────────────┐
│ SMALL_TALK?                 │
│  → Respond directly         │
└─────────────────────────────┘
```

There is **NO automatic fallback path**.

---

## 8. Core Agent Loop (LangChain)

```python
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

llm = ChatOpenAI(temperature=0)

class ElevixAgent:
    def __init__(self, rag_tool, web_search_tool):
        self.rag_tool = rag_tool
        self.web_search_tool = web_search_tool

    def handle_query(self, user_query: str):
        intent = classify_intent(user_query)

        if intent == "HR_POLICY":
            result = self.rag_tool.run(
                query=user_query,
                chat_history=memory.chat_memory.messages
            )

            if not result["has_context"]:
                return "I couldn't find this information in the company documents."

            return result["answer"]

        if intent == "GENERAL_FACT":
            return self.web_search_tool.run(user_query)

        return self.respond_small_talk(user_query)
```

This is the **entire intelligence** of ELEVIX.

---

## 9. Conversational Tone Enforcement

Small talk and responses must:
- Sound human
- Stay professional
- Avoid over‑verbosity

Example:

> "Good evening. I can help with HR policies, leave information, or general questions."

The agent **never reveals tool mechanics**.

---

## 10. Failure Modes (Handled Explicitly)

| Failure | Agent Response |
|------|---------------|
| HR info missing | Explicit refusal |
| Ambiguous intent | Ask clarification |
| Tool error | Apologize + stop |
| Empty input | Prompt user politely |

---

## 11. What Makes This Fool‑Proof

- No tool auto‑chaining
- No web fallback for HR
- No hallucination path
- Intent gate before tools
- Refusal is a valid outcome

This agent can **only be as smart as the documents**, which is exactly what HR requires.

---

## 12. Ready for Integration

Once tools are ready, plug them in:

```python
agent = ElevixAgent(
    rag_tool=HRRAGTool(),
    web_search_tool=WebSearchTool()
)
```

No agent rewrite required.

---

## Final Statement

ELEVIX is not a chatbot.

It is a **controlled decision system** that happens to speak politely.

If it does not know something, it stops.
That is intentional.
That is safe.

