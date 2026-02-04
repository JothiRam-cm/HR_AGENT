from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Define intents
INTENT_HR_POLICY = "HR_POLICY"
INTENT_GENERAL_FACT = "GENERAL_FACT"
INTENT_SMALL_TALK = "SMALL_TALK"

TEMPLATE = """
You are the intent classifier for the ELEVIX HR Assistant.
Your job is to determine the intent of the user's latest query, considering the conversation history.

Categories:
1. HR_POLICY: Questions about leave, holiday, PTO, sick leave, HR policy, benefits, payroll, internal rules, approvals.
2. GENERAL_FACT: Questions about public facts, who is/what is, weather, location, dates, public company info.
3. SMALL_TALK: Greetings, thanks, confirmations, ambiguous or conversational inputs.

Context Awareness:
- If the user's query is a follow-up (e.g., "What about casual leave?"), use the conversation history to determine the context.
- If the previous topic was HR policies, follow-ups are likely HR_POLICY.

Conversation History:
{chat_history}

User Query: {query}

Return ONLY the category name (HR_POLICY, GENERAL_FACT, or SMALL_TALK). Do not add any explanation.
Intent:
"""

def classify_intent(user_query: str, chat_history: str = "", llm=None) -> str:
    """
    Classifies the user query into one of the supported intents.
    Uses the provided LLM or defaults to ChatOpenAI.
    """
    if llm is None:
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
        except Exception:
            return _heuristic_intent(user_query)

    prompt = PromptTemplate(template=TEMPLATE, input_variables=["query", "chat_history"])
    chain = prompt | llm | StrOutputParser()
    
    try:
        intent = chain.invoke({"query": user_query, "chat_history": chat_history}).strip()
        if intent not in [INTENT_HR_POLICY, INTENT_GENERAL_FACT, INTENT_SMALL_TALK]:
            return INTENT_SMALL_TALK
        return intent
    except Exception as e:
        print(f"Intent classification failed: {e}. Using heuristic fallback.")
        return _heuristic_intent(user_query)

def _heuristic_intent(query: str) -> str:
    """Fallback keyword-based classification."""
    q = query.lower()
    hr_keywords = ["leave", "policy", "vacation", "sick", "approval", "hr", "benefit", "payroll"]
    fact_keywords = ["weather", "who is", "what is", "capital", "population"]
    
    for k in hr_keywords:
        if k in q:
            return INTENT_HR_POLICY
            
    for k in fact_keywords:
        if k in q:
            return INTENT_GENERAL_FACT
            
    return INTENT_SMALL_TALK
