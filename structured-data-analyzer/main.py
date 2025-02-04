import sys
import asyncio
from tools.helper import load_from_gptscript_workspace
import os
from io import BytesIO
import pandas as pd


async def read_file_content() -> str:
    valid_extensions = [".xlsx", ".xls", ".csv", ".tsv"]
    input_file_path = os.getenv("INPUT_FILE")
    if input_file_path == "":
        raise Exception("Error: INPUT_FILE can't be empty.")
    if not input_file_path.endswith(tuple(valid_extensions)):
        raise Exception(f"Error: INPUT_FILE must be a valid file with one of the following extensions: {', '.join(valid_extensions)}")
    
    try:
        data = await load_from_gptscript_workspace(input_file_path)
        data = BytesIO(data)
        if input_file_path.endswith(".xlsx") or input_file_path.endswith(".xls"):
            df = pd.read_excel(data)
        elif input_file_path.endswith(".csv"):
            df = pd.read_csv(data)
        elif input_file_path.endswith(".tsv"):
            data = pd.read_csv(data, sep="\t")
        else:
            raise Exception(f"Error: Unsupported file extension: {input_file_path}")
        
        output = df.to_json()
        print(output)
        return output
    except Exception as e:
        raise Exception(f"Error: Failed to read file {input_file_path}.: {e}")
        
    

async def query_data():
    print("QueryData")
    return "QueryData"

async def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <tool_name>")
        sys.exit(1)

    command = sys.argv[1]

    match command:
        case "ReadFileContent":
            response = await read_file_content()
        case "QueryData":
            response = await query_data()
        case _:
            print(f"Unknown command: {command}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())