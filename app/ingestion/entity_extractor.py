from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from app.config import GROQ_API_KEY, GROQ_MODEL

class ExtractedConcept(BaseModel):
    name: str
    description: str = ""
    related_to: list[str] = Field(default_factory=list)

class ExtractionResult(BaseModel):
    concepts: list[ExtractedConcept] = Field(default_factory=list)

def extract_concepts(text: str):
    if not GROQ_API_KEY:
        return []
    llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0)
    extractor = llm.with_structured_output(ExtractionResult)
    prompt = (
        "Extract key technical concepts, protocols, algorithms, formulas, and named entities "
        "explicitly supported by this textbook passage. Keep names canonical. Add related_to "
        "only for relationships clearly stated in the passage. Do not infer unsupported facts.\n\n"
        + text[:12000]
    )
    result = extractor.invoke(prompt)
    return result.concepts
