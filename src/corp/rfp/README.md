# corp.rfp -- RFP Answering Agent

## What this module does

Answers RFP questions using the knowledge base. Retrieves relevant notes,
selects best answers, routes to appropriate LLM (Gemini/Claude/OpenAI),
generates formatted responses in Word/Excel, and anonymizes customer-specific
content.

## Key files

| File | What it does |
|------|-------------|
| llm_router.py | Route questions to KB sources + LLM models |
| answer_selector.py | Select and rank candidate answers |
| rfp_excel_agent.py | Generate RFP responses in Excel format |
| rfp_answer_word.py | Generate RFP responses in Word format |
| vault_adapter.py | Simplified vault access for RFP context |
| rfp_feedback.py | Response quality feedback tracking |
| validate_profiles.py | Validate product profile YAML files |
| anonymization/ | Customer name anonymization (config, blocklist) |

## Dependencies

- **Depends on:** corp.rfp internal, google-genai, anthropic, openai
- **Used by:** corp.cli.rfp, corp.retrieve.rfp

## Data flow

RFP question -> retrieve notes from index.db -> answer_selector ranks -> LLM generates answer -> Word/Excel output -> anonymize
