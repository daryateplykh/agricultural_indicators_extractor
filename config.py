import os
from dotenv import load_dotenv

load_dotenv()

class Configuration:
    API_KEY = os.getenv("API_KEY")
    CHROMA_PATH = "chroma"
    DATA_PATH = "data"
    OUTPUT_PATH = "output_chunks"

    KEYWORDS = ["not classified by size of holding", "Main Results"]

    COUNTRIES = ["AMERICAN SAMOA", "AFGHANISTAN", "ALBANIA", "ALGERIA",
         "Yemen Arab Republic", "AZERBAIJAN", "BANGLADESH",
         "BELGIUM", "Burkina Faso", "Cabo Verde",
         "Brazil", "Canada", "Benin",
         "Congo, Dem. Rep.", "Belgium",
         "Denmark", "Fiji", "Panama", "BOTSWANA", ""] 

    @classmethod
    def initialize(cls):
        os.makedirs(cls.OUTPUT_PATH, exist_ok=True) 