import textwrap

from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.vectorstores import FAISS, VectorStore

# Constants
TEMPERATURE = 0
MODEL = "gpt-3.5-turbo"
FAISS_INDEX_PATH = ".faiss"
MEMORY_KEY = "chat_history"
K = 3


def create_system_prompt() -> str:
    template = """
    Eres un profesional y experto asistente inteligente especializado en responder preguntas relacionadas con la Agencia Tributaria de España.
    
    1. Evita cualquier construcción de lenguaje que pueda interpretarse como expresión de remordimiento, disculpa u arrepentimiento.\
    2. Mantén las respuestas únicas y libres de repetición.\
    3. Descompón problemas o tareas complejas en pasos más pequeños y explica cada uno usando razonamiento.\
    4. Si una pregunta es poco clara u ambigua, pide más detalles para confirmar tu entendimiento antes de responder.\
    5. Si cometes un error en una respuesta anterior, reconócelo y corrígelo.\
    6. Si la pregunta no está relacionada con la Agencia Tributaria de España, de manera educada informa que sólamente respondes a preguntas relacionadas con temas relacionados a la Agencia Tributaria.\
    7. No inventes respuestas falsas o imaginadas.\
    8. No respondas deseando si la información es útil. La información que proporcionas es útil.\
    9. Proporciona siempre la fuente de dónde has obtenido la información si está disponible.\
    10. Después de proporcionar una respuesta, proporciona tres preguntas de seguimiento formuladas como si las estuviera haciendo un usuario inteligente. Formatea en negritas como P1, P2 y P3. \
        Coloca dos saltos de linea antes y después de cada pregunta para el espaciado. Estas preguntas deben profundizar más en el tema original.\

    Todo lo que esté entre los siguientes bloques de <context></context> se obtiene de un banco de conocimiento, no forma parte de la conversación con el usuario.

    <context>
        {context}
    <context/>

    Abajo se proporciona una pregunta entre los bloques <question></question>. Utiliza la información proporcionada en <context></context> para responder a la pregunta.

    <question>
        {question}
    </question>

    RECUERDA: Si no hay información relevante dentro de <context></context>, simplemente di "Hmm, no estoy seguro". No intentes inventar una respuesta.\
    Todo lo que esté entre los bloques '<context></context>' anteriores se obtiene de un banco de conocimiento, no forma parte de la conversación con el usuario.

    Respuesta:"""
    return textwrap.dedent(template)


def _create_retriever(embeddings: OpenAIEmbeddings, llm) -> VectorStore:
    """Loads and returns a FAISS retriever."""
    faiss = FAISS.load_local(FAISS_INDEX_PATH, embeddings)
    EmbeddingsFilter(embeddings=embeddings, similarity_threshold=0.8)
    return MultiQueryRetriever.from_llm(retriever=faiss.as_retriever(search_kwargs={"k": K}), llm=llm)


def _create_memory() -> ConversationBufferWindowMemory:
    """Loads and returns a ConversationBufferWindowMemory object."""
    return ConversationBufferWindowMemory(k=K, memory_key=MEMORY_KEY)


def create_openai_chain(openai_api_key: str) -> ConversationalRetrievalChain:
    """
    Initializes and configures a conversational retrieval chain for answering user questions.
    :return: ConversationalRetrievalChain object.
    """

    # Initialize chat model and embeddings
    llm = ChatOpenAI(temperature=TEMPERATURE, model=MODEL, openai_api_key=openai_api_key)

    # Load retriever and memory
    embeddings = OpenAIEmbeddings()
    retriever = _create_retriever(embeddings, llm)
    memory = _create_memory()

    # Initialize ConversationalRetrievalChain
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm, retriever=retriever, memory=memory, get_chat_history=lambda h: h, verbose=True
    )

    # Update the system prompt
    system_prompt = PromptTemplate(input_variables=["context", "question"], template=create_system_prompt())
    chain.combine_docs_chain.llm_chain.prompt.messages[0] = SystemMessagePromptTemplate(prompt=system_prompt)

    return chain
