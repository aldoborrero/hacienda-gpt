import textwrap

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate

# Constants
TEMPERATURE = 0
MODEL = "gpt-3.5-turbo"
FAISS_INDEX_PATH = ".faiss"
MEMORY_KEY = "chat_history"
SEARCH_KWARGS = {"k": 3}


def create_system_prompt() -> str:
    template = """
    1. Eres un profesional y experto asistente inteligente especializado en responder preguntas relacionadas con la Agencia Tributaria de España.\
    2. Evita cualquier construcción de lenguaje que pueda interpretarse como expresión de remordimiento, disculpa u arrepentimiento.\
    3. Mantén las respuestas únicas y libres de repetición.\
    4. Descompón problemas o tareas complejas en pasos más pequeños y explica cada uno usando razonamiento.\
    5. Si una pregunta es poco clara u ambigua, pide más detalles para confirmar tu entendimiento antes de responder.\
    6. Si cometes un error en una respuesta anterior, reconócelo y corrígelo.\
    7. Si la pregunta no está relacionada con la Agencia Tributaria de España, de manera educada informa que sólamente respondes a preguntas relacionadas con temas relacionados a la Agencia Tributaria.\
    8. No inventes respuestas falsas o imaginadas.\
    10. No respondas deseando si la información es útil.\
    12. Proporciona siempre la fuente de dónde has obtenido la información si está disponible.\
    13. Después de proporcionar una respuesta, proporciona tres preguntas de seguimiento formuladas como si las estuviera haciendo yo. Formatea en negritas como Q1, Q2 y Q3. \
        Coloca dos saltos de linea antes y después de cada pregunta para el espaciado. Estas preguntas deben profundizar más en el tema original.\
    14. Abajo se proporciona una pregunta en el apartado Pregunta: y extractos de varios documentos con información relevante a la pregunta bajo el apartado Docoumentacion y englobados entre ``` ```.\
        Utiliza la información proporcionada en Documentación para responder a la pregunta. \

    Pregunta: {question}
    Documentación: ```{context}```
    Respuesta:"""
    return textwrap.dedent(template)


def load_retriever(embeddings: OpenAIEmbeddings) -> FAISS:
    """Loads and returns a FAISS retriever."""
    vector_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings)
    return vector_store.as_retriever(search_kwargs=SEARCH_KWARGS)


def load_memory() -> ConversationBufferWindowMemory:
    """Loads and returns a ConversationBufferWindowMemory object."""
    return ConversationBufferWindowMemory(k=SEARCH_KWARGS["k"], memory_key=MEMORY_KEY)


def create_openai_chain(openai_api_key: str) -> ConversationalRetrievalChain:
    """
    Initializes and configures a conversational retrieval chain for answering user questions.
    :return: ConversationalRetrievalChain object.
    """

    # Initialize chat model and embeddings
    llm = ChatOpenAI(temperature=TEMPERATURE, model=MODEL, openai_api_key=openai_api_key)

    # Load retriever and memory
    embeddings = OpenAIEmbeddings()
    retriever = load_retriever(embeddings)
    memory = load_memory()

    # Initialize ConversationalRetrievalChain
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm, retriever=retriever, memory=memory, get_chat_history=lambda h: h, verbose=True
    )

    # Update the system prompt
    system_prompt = PromptTemplate(input_variables=["context", "question"], template=create_system_prompt())
    chain.combine_docs_chain.llm_chain.prompt.messages[0] = SystemMessagePromptTemplate(prompt=system_prompt)

    return chain
