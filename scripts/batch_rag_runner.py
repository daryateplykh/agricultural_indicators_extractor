import yaml
import re
import os
from datetime import datetime
from src.rag_core.rag_answer import query_rag

def format_number_with_commas(value, column_name=""):
    if column_name.lower() in ['year', 'год', 'year_']:
        return value
    
    if isinstance(value, str):
        cleaned = re.sub(r'[,\s]', '', value)
        try:
            num = float(cleaned)
            if num.is_integer():
                return f"{int(num):,}".replace(",", " ")
            else:
                return f"{num:,.2f}".replace(",", " ")
        except ValueError:
            return value
    return value

class BatchRAGRunner:
    def __init__(self, config_path):
        config_path = os.path.join('scripts', config_path)
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.queries = self.config["queries"]
        self.indicators = self.config["indicators"]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"rag_output_{timestamp}"
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        for q in self.queries:
            country = q["country"]
            years = q["years"]
            for indicator in self.indicators:
                if indicator is None or not indicator.strip():
                    continue
                
                if len(years) == 1:
                    question = f"What is the {indicator} in {country} in {years[0]}?"
                    filename_suffix = f"{years[0]}"
                else:
                    years_str = " and ".join(map(str, years))
                    question = f"What are the {indicator} data for {country} across {years_str}? Please provide all available data for both years, including any differences in parameters between the years."
                    filename_suffix = "_".join(map(str, years))
                
                print(f"\n=== Question: {question}")
                answer = query_rag(question, save_csv=False)
                safe_country = re.sub(r"[^\w\-]", "_", country)
                safe_indicator = re.sub(r"[^\w\-]", "_", indicator)
                filename = os.path.join(self.output_dir, f"output_{safe_country}_{filename_suffix}_{safe_indicator}.csv")
                table_lines = [line for line in answer.splitlines() if "|" in line]
                table_lines = [line for line in table_lines if not re.match(r"^\s*\|?\s*-+\s*\|", line)]
                if len(table_lines) >= 2:
                    headers = [cell.strip() for cell in table_lines[0].split("|") if cell.strip()]
                    rows = []
                    for row_line in table_lines[1:]:
                        row = [cell.strip() for cell in row_line.split("|") if cell.strip()]
                        if len(row) != len(headers):
                            if len(row) > len(headers):
                                row = row[:len(headers)]
                            else:
                                while len(row) < len(headers):
                                    row.append("")
                        rows.append(row)
                    import pandas as pd
                    df = pd.DataFrame(rows, columns=headers)
                    
                    for column in df.columns:
                        df[column] = df[column].apply(lambda x: format_number_with_commas(x, column))
                    
                    df.to_csv(filename, index=False)
                else:
                    print(f"Table not found, CSV not created {filename}.")

if __name__ == "__main__":
    runner = BatchRAGRunner("queries.yaml")
    runner.run() 