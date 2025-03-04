from load_text import load_text_from_file
from helper import setup_logger, get_openai_client
from summarize import DocumentSummarizer, MODEL, TIKTOKEN_MODEL, MAX_CHUNK_TOKENS, MAX_WORKERS
import os
import tiktoken

logger = setup_logger(__name__)

TIKTOKEN_MODEL = "gpt-4o"
enc = tiktoken.encoding_for_model(TIKTOKEN_MODEL)
TOKEN_THRESHOLD = 10000

async def main():
    input_file = os.getenv("INPUT_FILE", "")
    if not input_file:
        raise ValueError("Error: INPUT_FILE environment variable is not set")

    file_content = await load_text_from_file(input_file)
    tokens = enc.encode(file_content)
    
    if len(tokens) > TOKEN_THRESHOLD: # if the file has too many tokens, summarize it
        summarizer = DocumentSummarizer(
            get_openai_client(),
            model=MODEL,
            max_chunk_tokens=MAX_CHUNK_TOKENS,
            max_workers=MAX_WORKERS,
        )
        try:
            final_summary = summarizer.summarize(file_content)
        except Exception as e:
            raise Exception(f"ERROR: Summarization failed: {e}")
        
        response_str = f"Uploaded file {input_file} contains {len(tokens)} tokens.\n\n"
        response_str += f"Summary of the file content:\n\n{final_summary}"
        print(response_str)
        return response_str
    else: # if the file has less than TOKEN_THRESHOLD tokens, directly return the file content
        print(file_content)
        return file_content