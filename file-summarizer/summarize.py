#!/usr/bin/env python3
import asyncio
import tiktoken
from typing import List
import concurrent.futures
import sys
import os
from helper import load_from_gptscript_workspace, save_to_gptscript_workspace


MAX_CONTEXT_TOKENS = 128000
MAX_OUTPUT_TOKENS = 16384
OVERHEAD_TOKENS = 2000
MAX_CHUNK_TOKENS = MAX_CONTEXT_TOKENS - MAX_OUTPUT_TOKENS - OVERHEAD_TOKENS
MAX_WORKERS = 4
MODEL = os.getenv("OBOT_DEFAULT_LLM_MODEL", "gpt-4o") # TODO: this should be the same model from obot user selected model provider.

class DocumentSummarizer:
    """
    Summarizes very large documents with hierarchical chunking using gpt-4o.
    Supports parallel calls to speed up summarization.
    Optionally uses a 'topic' for specialized focus and structure.
    """

    def __init__(
        self,
        client,
        model: str = MODEL,
        max_context_tokens: int = MAX_CONTEXT_TOKENS,
        max_output_tokens: int = MAX_OUTPUT_TOKENS,
        overhead_tokens: int = OVERHEAD_TOKENS,
        max_chunk_tokens: int = MAX_CHUNK_TOKENS,
        max_workers: int = MAX_WORKERS,
        verbose: bool = False,
    ):
        """
        :param client: An OpenAI() client instance (from openai import OpenAI).
        :param model: Model name (e.g., 'gpt-4o'), must be valid for encoding_for_model().
        :param max_context_tokens: Maximum context length for GPT-4o (default: 128000).
        :param max_output_tokens: Maximum tokens GPT-4o can generate (default: 16384).
        :param overhead_tokens: Token buffer for system/developer instructions, etc. (default: 2000).
        :param max_chunk_tokens: Maximum tokens per chunk (default: max_context_tokens - max_output_tokens - overhead_tokens).
        :param max_workers: Number of parallel threads for summarization calls (default: 4).
        :param verbose: Whether to print additional logs and progress information.
        """
        self.client = client
        self.model = model
        self.max_context_tokens = max_context_tokens
        self.max_output_tokens = max_output_tokens
        self.overhead_tokens = overhead_tokens
        self.max_workers = max_workers
        self.verbose = verbose

        # Load the tokenizer for the specified model
        self.enc = tiktoken.encoding_for_model(self.model)

        # Calculate or use provided max chunk size
        default_chunk_size = (
            self.max_context_tokens - self.max_output_tokens - self.overhead_tokens
        )
        self.max_chunk_size = (
            max_chunk_tokens if max_chunk_tokens is not None else default_chunk_size
        )

        if self.max_chunk_size <= 0:
            raise ValueError(
                "Calculated or provided max_chunk_size is non-positive. "
                "Adjust max_chunk_tokens or reduce overhead_tokens/max_output_tokens."
            )

        if self.verbose:
            print(f"[DEBUG] Using model: {self.model}")
            print(f"[DEBUG] max_context_tokens: {self.max_context_tokens}")
            print(f"[DEBUG] max_output_tokens: {self.max_output_tokens}")
            print(f"[DEBUG] overhead_tokens: {self.overhead_tokens}")
            print(f"[DEBUG] max_chunk_size: {self.max_chunk_size}")
            print(f"[DEBUG] max_workers: {self.max_workers}")

    def chunk_text(self, text: str) -> List[str]:
        """
        Splits text into token-based chunks, ensuring each chunk fits within
        (max_context_tokens - overhead_tokens - max_output_tokens).
        """
        tokens = self.enc.encode(text)
        chunks = []

        if self.verbose:
            print(f"[DEBUG] Total tokens in document: {len(tokens)}")
            print("[DEBUG] Splitting into chunks...")

        for i in range(0, len(tokens), self.max_chunk_size):
            chunk_slice = tokens[i : i + self.max_chunk_size]
            chunk_text = self.enc.decode(chunk_slice)
            chunks.append(chunk_text)

        if self.verbose:
            print(f"[DEBUG] Created {len(chunks)} chunk(s).")

        return chunks

    def summarize_chunk(self, chunk: str) -> str:
        """
        Summarizes a single chunk using an intensive, detail-preserving prompt.
        """
        system_prompt = """You are an expert in information preservation and technical documentation.
Your task is to create a dense, detailed retention of the input content.

Critical rules:

1. PRESERVE ALL:
   - Technical specifications, numbers, and measurements
   - Names, identifiers, key terms
   - Procedural steps and sequences
   - Relationships and dependencies
   - Configuration details and parameters
   - Important direct quotes

2. Structure your response as:
   <METADATA>
   - Document type: (code/technical/narrative/documentation/other)
   - Key terms: [list important terms/identifiers]
   - Structure type: (hierarchical/sequential/reference/other)
   </METADATA>

   <CORE_CONTENT>
   [Detailed preservation of the content, maintaining original structure if possible]
   </CORE_CONTENT>

   <RELATIONSHIPS>
   [Dependencies, connections, cross-references found in the content]
   </RELATIONSHIPS>

3. Use direct quotes where precision matters
4. Maintain hierarchical structure if it exists
5. Preserve all numeric/technical data
6. Keep lists, tables, or structured data in original format if feasible"""

        user_prompt = f"""Analyze and preserve this content with maximum detail:

{chunk}

Remember:
- Maintain original structure
- Retain all numeric values
- Include complete lists/tables
- Use quotes for critical data
- Keep relationships and dependencies
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=self.max_output_tokens,
        )
        return response.choices[0].message.content.strip()

    def summarize_chunks_in_parallel(self, chunks: List[str]) -> List[str]:
        """
        Summarize multiple chunks in parallel using ThreadPoolExecutor.
        """
        if self.verbose:
            print("[DEBUG] Starting multi-pass summarization...")
        summaries = []
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # Dispatch summarization tasks
            future_to_chunk = {
                executor.submit(self.summarize_chunk, chunk): chunk for chunk in chunks
            }
            for future in concurrent.futures.as_completed(future_to_chunk):
                summaries.append(future.result())

        if self.verbose:
            print(f"[DEBUG] Summarized {len(chunks)} chunk(s) in parallel.")

        return summaries


    def final_reduction(self, text: str) -> str:
        """
        Produces a final, consolidated version of the retained information.
        Maintains maximum detail in a cohesive format.
        """
        system_prompt = """You are creating the final consolidated version of preserved information. 
Preserve maximum detail and maintain a cohesive structure.

Requirements:

1. DO NOT summarize away critical details
2. Keep ALL:
   - Technical specs, numeric values
   - Names and IDs
   - Procedural steps
   - Configuration details
   - Interrelationships

3. Use markdown for clarity
4. Preserve essential formatting
5. Keep direct quotes intact
"""

        user_prompt = f"""Consolidate the following retention text into a single, cohesive document, 
while preserving all critical information:

{text}

You must:
- Retain specificity
- Keep numeric values
- Use direct quotes where originally present
- Maintain references, relationships, and any structured data
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=self.max_output_tokens,
        )
        return response.choices[0].message.content.strip()
    
    def iterative_summarize(self, text_to_summarize: str) -> str:
        """
        Recursively summarizes the text and merges the summaries until it is reduced to a single (summary) chunk.
        """

        chunks = self.chunk_text(text_to_summarize)
        # if there is only one chunk, we are done
        if len(chunks) <= 1:
            return text_to_summarize

        # Otherwise, split the text into chunks and summarize them in parallel
        next_level_summaries = self.summarize_chunks_in_parallel(chunks)
        if self.verbose:
            print(f"[DEBUG] Combining {len(next_level_summaries)} summaries into a new text...")
        return self.iterative_summarize("\n\n".join(next_level_summaries))


    def summarize(self, document_text: str) -> str:
        """
        Main entry point for summarization:
        1) Recursively merge until single summary/chunk with less than MAX_CHUNK_TOKENS remains
        2) Perform final reduction for a cohesive, detail-rich result
        """
        reduced_summary = self.iterative_summarize(document_text)
        final_summary = self.final_reduction(reduced_summary)
        return final_summary


async def main():
    input_file = os.getenv("INPUT_FILE", "")
    if not input_file:
        raise ValueError("INPUT_FILE environment variable is not set")
    try:
        file_content = await load_from_gptscript_workspace(input_file)
    except Exception as e:
        raise ValueError(f"Failed to load file from GPTScript workspace file {input_file}, Error: {e}")
    if len(file_content) == 0:
        print("File is empty, skipping summarization")
        return
    
    output_file = os.getenv("OUTPUT_FILE", "")
    
    # Check for OPENAI_API_KEY
    if "OPENAI_API_KEY" not in os.environ:
        sys.exit(
            "ERROR: OPENAI_API_KEY environment variable not found.\n"
            "Please set it before running the script, e.g.:\n\n"
            "  export OPENAI_API_KEY='sk-xxxxxxx'\n"
        )
        
    # This is a must have because we are using the same model as the obot user selected model provider.
    if "OPENAI_BASE_URL" not in os.environ:
        sys.exit(
            "ERROR: OPENAI_BASE_URL environment variable not found.\n"
            "Please set it before running the script, e.g.:\n\n"
            "  export OPENAI_BASE_URL='https://api.openai.com/v1'\n"
        )

    # Initialize OpenAI client
    try:
        from openai import OpenAI

        client = OpenAI(base_url=os.environ["OPENAI_BASE_URL"], api_key=os.environ["OPENAI_API_KEY"])  # Uses OPENAI_API_KEY from environment
    except Exception as e:
        raise Exception(f"ERROR: Failed to initialize OpenAI client: {e}")

    # Create summarizer and process document
    summarizer = DocumentSummarizer(
        client,
        model=MODEL,
        max_chunk_tokens=MAX_CHUNK_TOKENS,
        max_workers=MAX_WORKERS,
        verbose=False,
    )

    try:
        final_summary = summarizer.summarize(file_content)
    except Exception as e:
        raise Exception(f"ERROR: Summarization failed: {e}")

    # Handle output
    if output_file:
        try:
            await save_to_gptscript_workspace(output_file, final_summary)
            print(f"Summary written to workspace file: {output_file}")
        except Exception as e:
            print(f"File Summary:\n{final_summary}")
            raise Exception(f"Failed to save summary to GPTScript workspace file {output_file}, Error: {e}")
    else:
        print(final_summary)


if __name__ == "__main__":
    asyncio.run(main())