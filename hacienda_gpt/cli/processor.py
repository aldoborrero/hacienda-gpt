import logging
import os

import click

from hacienda_gpt.processor.document_loader import (
    process_with_gpt4all,
    process_with_openai,
)
from hacienda_gpt.utils import configure_logging

PRJ_DATA_DIR = os.environ.get("PRJ_DATA_DIR", os.path.expanduser("~"))
FAISS_DIR = os.path.join(PRJ_DATA_DIR, "faiss")
CONTENT_DIR = os.path.join(PRJ_DATA_DIR, "html")


@click.command()
@click.option("--content-dir", type=click.Path(exists=True, file_okay=False, dir_okay=True), default=CONTENT_DIR)
@click.option("--output-dir", type=click.Path(exists=False, file_okay=False, dir_okay=True), default=FAISS_DIR)
@click.option("--chunk-size", type=click.IntRange(min=0), default=1500)
@click.option("--chunk-overlap", type=click.IntRange(min=0), default=0)
@click.option("--overwrite-output", is_flag=True)
@click.option("--embedder", type=click.Choice(["openai", "gpt4all"], case_sensitive=False), default="gpt4all")
def cli(content_dir, output_dir, chunk_size, chunk_overlap, overwrite_output, embedder):
    configure_logging()

    if not overwrite_output and os.path.exists(output_dir) and os.listdir(output_dir):
        logging.error(f"Directory {output_dir} exists and contains files. Aborting.")
        return

    args = {
        "content_dir": content_dir,
        "output_dir": output_dir,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
    }

    (process_with_openai if embedder == "openai" else process_with_gpt4all)(args)

    logging.info("Local FAISS index has been successfully saved")


if __name__ == "__main__":
    cli()
