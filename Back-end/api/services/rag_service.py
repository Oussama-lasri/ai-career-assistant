import os 
from langchain_openai import OpenAIEmbeddings ,ChatOpenAI
from langchain.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage 
from langchain_core.prompts import PromptTemplate


current_dir = os.path.dirname(os.path.abspath(__file__))


class RAGService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.db_dir = os.path.join(current_dir, "db") 
        self.model = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
        )
    
        self.services = {
                "answer_question": self._default_system_prompt(),
                "rate_resume": self._rate_resume_prompt(),
                "suggest_improvements": self._improve_resume_prompt(),
                "analyze_skills": self._analyze_skills_prompt(),
            }

    def _default_system_prompt(self):
        return (
            "You are a helpful AI career assistant that provides personalized answers "
            "based on the user's resume. Only answer based on resume context. If info is missing, say so. "
            "Use a professional and supportive tone."
        )

    def _rate_resume_prompt(self):
        return (
            "You are an expert resume reviewer. Rate the resume on a scale from 1 to 10 in the following areas: "
            "- Clarity and formatting\n- Relevance of experience\n- Use of keywords\n- Presentation of skills\n"
            "Then explain your reasoning in detail."
        )

    def _improve_resume_prompt(self):
        return (
            "You are a resume improvement assistant. Based on the resume context, suggest improvements in formatting, "
            "content, structure, or language. Use bullet points where possible."
        )

    def _analyze_skills_prompt(self):
        return (
            "You are a career assistant specialized in skills analysis. Identify the key hard and soft skills in the resume. "
            "List them under separate headings. Be specific."
        )

    def build_human_prompt(self, context: str, question: str) -> str:
        return f"""Here is the resume context:\n\n{context}\n\nUser's question: {question}"""

    def ask_model(self, context: str, question: str , service_type: str = "answer_question"):
        # .get(service_type, fallback)
        system_prompt = self.services.get(service_type, self._default_system_prompt)()
        human_prompt = self.build_human_prompt(context, question)

        response = self.model.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ])
        return response