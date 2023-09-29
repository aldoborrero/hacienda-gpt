from typing import List
import os
import logging
import click
import openai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.docstore.document import Document

# Constants
PRJ_ROOT = os.environ.get("PRJ_ROOT", os.path.expanduser("~"))
FAISS_DIR = os.path.join(PRJ_ROOT, ".faiss")
CONTENT_DIR = os.path.join(PRJ_ROOT, "content")


def initialize_logging():
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s", level=logging.INFO
    )

def load_documents(directory: str, chunk_size: int, chunk_overlap: int) -> List[Document]:
    """Loads documents from a given directory."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    loader = PyPDFDirectoryLoader(directory)
    return loader.load_and_split(text_splitter)


def get_openai_api_key():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logging.error("OPENAI_API_KEY missing!")
        exit(1)
    return api_key


@click.command(help="This command performs text analysis and saves FAISS index.")
@click.option(
    "--content-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=CONTENT_DIR,
    show_default=True,
    help="Directory containing the content to be processed.",
)
@click.option(
    "--output-dir",
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    default=FAISS_DIR,
    show_default=True,
    help="Directory where the FAISS index will be saved.",
)
@click.option("--chunk-size", type=click.IntRange(min=0), default=1500, help="Size of each text chunk to be processed.")
@click.option(
    "--chunk-overlap", type=click.IntRange(min=0), default=0, help="Number of overlapping characters between chunks."
)
@click.option("--overwrite-output", is_flag=True, help="Flag to indicate whether to overwrite existing FAISS index.")
def cli(content_dir: str, output_dir: str, chunk_size: int, chunk_overlap: int, overwrite_output: bool) -> None:
    # Initialize logging
    initialize_logging()

    # Check for existing FAISS directory and files within
    if not overwrite_output and os.path.exists(output_dir) and os.listdir(output_dir):
        logging.error(
            f"Directory {output_dir} exists and contains files, but the overwrite flag is not enabled. Aborting."
        )
        return

    # Load PDF documents
    logging.info(f"Loading documents from {content_dir}")
    docs = load_documents(content_dir=content_dir, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # Initialize OpenAI embedding model
    embeddings = OpenAIEmbeddings(openai_api_key=get_openai_api_key())

    # Create or load FAISS index
    db = FAISS.from_documents(docs, embeddings)
    db.save_local(output_dir)

    logging.info("Local FAISS index has been successfully saved")


if __name__ == "__main__":
    cli()
