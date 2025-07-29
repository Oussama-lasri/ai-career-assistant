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

    def build_system_prompt(self) -> str:
        return (
            "You are a helpful AI career assistant that provides personalized answers "
            "based on the user's resume.\n\n"
            "Instructions:\n"
            "- ONLY answer based on the content found in the resume context.\n"
            "- If the information is not available in the resume, clearly respond with: "
            "\"Information not found in the resume.\"\n"
            "- Do not make assumptions or hallucinate facts.\n"
            "- Be professional, supportive, and conversational in tone.\n"
            "- Provide specific details from the resume whenever possible (e.g., job titles, companies, dates, skills, certifications, projects).\n"
            "- When asked about experience, reference relevant work history, education, or projects from the resume.\n"
            "- If something is missing or could be improved, provide constructive suggestions for enhancing the resume.\n"
            "- Structure responses clearly. Use bullet points or headings if needed to improve readability.\n"
            "\nAlways ensure that your answers are grounded in the resume context provided."
        )

    def build_human_prompt(self, context: str, question: str) -> str:
        return f"""Here is the resume context:\n\n{context}\n\nUser's question: {question}"""

    def ask_model(self, context: str, question: str):
        system_prompt = self.build_system_prompt()
        human_prompt = self.build_human_prompt(context, question)

        response = self.model.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ])
        return response