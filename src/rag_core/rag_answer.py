import argparse
import os
import re
import pandas as pd
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from together import Together
from config import Configuration


load_dotenv()

PROMPT_TEMPLATE = """
You are a data assistant for agricultural census reports.
Use only the context below to answer the question.

If the question includes multiple countries or multiple indicators, 
return **all available values** for each **country separately**.

If the question asks about data across multiple years, note that different years may have different parameters or indicators available. 
Include all available data for each year, even if the parameters differ between years.

Please format your answer as a Markdown table with the following columns:
| Country | Year | Indicator | Value | Unit |

Group all indicators by country - do not mix countries and do not create extra combinations.

{context}

---

Answer the question based on the above context: {question}
"""

def get_embedding_function():
    return HuggingFaceEmbeddings(model_name=Configuration.EMBEDDING_MODEL)

def query_rag(query_text: str, country: str, year: int, save_csv: bool = True) -> str:
    embedding_function = get_embedding_function()
    db = Chroma(
        persist_directory=Configuration.CHROMA_PATH,
        embedding_function=embedding_function
    )

    filter_criteria = {
        "$and": [
            {"country": {"$eq": country}},
            {"year": {"$eq": str(year)}}
        ]
    }
    
    results = db.similarity_search_with_score(query_text, k=5, filter=filter_criteria)
    if not results:
        print(f"No matching documents found for country '{country}' and year '{year}'.")
        return ""

    context_text = "\\n\\n---\\n\\n".join([doc.page_content for doc, _ in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)

    
    client = Together(api_key=Configuration.TOGETHER_API_KEY)  
    try:
        response = client.chat.completions.create(
            model=Configuration.LLM_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024,
            temperature=0.2,
            top_p=0.7
        )
        answer = response.choices[0].message.content.strip()
        print("\\nAnswer:\\n", answer)
    except Exception as e:
        print("Error from Together API:", e)
        return ""

    if save_csv:
        table_lines = [line for line in answer.splitlines() if "|" in line]
        table_lines = [line for line in table_lines if not re.match(r"^\\s*\\|?\\s*-+\\s*\\|", line)]

        if len(table_lines) >= 2:
            headers = [cell.strip() for cell in table_lines[0].split("|") if cell.strip()]
            rows = []
            for row_line in table_lines[1:]:
                row = [cell.strip() for cell in row_line.split("|") if cell.strip()]
                while len(row) < len(headers):
                    row.append("")
                rows.append(row)

            df = pd.DataFrame(rows, columns=headers)
            df.to_csv("output.csv", index=False)

    return answer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
 
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    total_chunks = len(db.get()["ids"])


if __name__ == "__main__":
    main() 