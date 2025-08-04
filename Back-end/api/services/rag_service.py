import os 
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage 
from langchain_core.prompts import PromptTemplate
from ..utils.document_processing_service import DocumentProcessingService 


current_dir = os.path.dirname(os.path.abspath(__file__))


class RAGService:
    def __init__(self):
        # self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2") 

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

    def ask_model_with_question(self, context: str, question: str, service_type: str = "answer_question"):
        """Ask model with both context and a specific question"""
        print(f"\n=== ASKING MODEL WITH QUESTION ===")
        print(f"Context length: {len(context)} characters")
        print(f"Question: {question}")
        print(f"Service type: {service_type}")
        
        try:
            system_prompt = self.services.get(service_type, self._default_system_prompt())
            print(f"Using system prompt: {system_prompt}")
            human_prompt = self.build_human_prompt(context, question)

            response = self.model.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ])
            return response
        except Exception as e:
            return f"Error during model invocation: {e}"
        
    def ask_model(self, context: str, service_type):
        """Ask model with just context (for services like rating, analysis, etc.)"""
        print(f"\n=== ASKING MODEL ===")
        print(f"Context length: {len(context)} characters")
        print(f"Service type: {service_type}")
        
        try:
            if not context.strip():
                raise ValueError("Resume context is empty. Cannot proceed.")
            system_prompt = self.services.get(service_type, self._default_system_prompt())
            print(f"Using system prompt: {system_prompt}")
            
            response = self.model.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=context),
            ])
            return response
        except Exception as e:
            return f"Error during model invocation: {e}"

    def load_vectorstore(self):
        """Load the Chroma vector database"""
        try:
            vectorstore = Chroma(
                persist_directory=self.db_dir,
                embedding_function=self.embeddings
            )
            return vectorstore
        except Exception as e:
            print(f"Error loading vectorstore: {e}")
            return None

    def retrieve_context(self, query: str, k: int = 5):
        """Retrieve relevant context from the vector database"""
    
        vectorstore = DocumentProcessingService.get_vector_store(f"resume_{str(6)}")
        
        if vectorstore is None:
            return "No context available - vectorstore could not be loaded."
        
        try:
            docs = vectorstore.similarity_search(query, k=k)
            context = "\n\n".join([doc.page_content for doc in docs])
            return context
        except Exception as e:
            return f"Error retrieving context: {e}"

    def get_response(self, question: str, service_type: str = "answer_question", k: int = 5):
        """Complete RAG pipeline: retrieve context and generate response"""
        # Retrieve relevant context
        print(f"\n=== RETRIEVING CONTEXT ===")
        print(f"Question: {question}")
        
        context = self.retrieve_context(question, k=k)
        
        # Generate response based on service type
        if service_type == "answer_question":
            return self.ask_model_with_question(context, question, service_type)
        else:
            return self.ask_model(context, service_type)