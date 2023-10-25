import logging

from langchain.docstore.document import Document
from langchain.document_loaders import DirectoryLoader
from langchain.embeddings import GPT4AllEmbeddings, OpenAIEmbeddings
from langchain.schema.embeddings import Embeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS

from hacienda_gpt.utils import get_openai_api_key


class DocumentProcessor:
    def __init__(
        self,
        embeddings: type[Embeddings],
        content_dir: str,
        output_dir: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 0,
        glob: str = "**/*.html",
    ) -> None:
        self.embeddings = embeddings
        self.content_dir = content_dir
        self.output_dir = output_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.glob = glob

    def _create_text_splitter(self) -> RecursiveCharacterTextSplitter:
        return RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)

    def _create_loader(self) -> DirectoryLoader:
        return DirectoryLoader(path=self.content_dir, glob=self.glob, use_multithreading=True, show_progress=True)

    def _load_and_split(self) -> list[Document]:
        return self._create_loader().load_and_split(self._create_text_splitter())

    def process_documents(self) -> None:
        logging.info(f"Loading documents from {self.content_dir}")
        db = FAISS.from_documents(self._load_and_split(), self.embeddings)
        db.save_local(self.output_dir)
        logging.info("Local FAISS index successfully saved")


def process_with_openai(args: dict) -> None:
    processor = DocumentProcessor(OpenAIEmbeddings(get_openai_api_key()), **args)
    processor.process_documents()


def process_with_gpt4all(args: dict) -> None:
    processor = DocumentProcessor(GPT4AllEmbeddings(), **args)
    processor.process_documents()
