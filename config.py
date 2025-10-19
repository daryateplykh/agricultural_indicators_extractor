import os
from dotenv import load_dotenv

load_dotenv()

class Configuration:
    API_KEY = os.getenv("API_KEY")
    TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
    
    CHROMA_PATH = "chroma"
    DATA_PATH = "data"
    OUTPUT_PATH = "output_chunks"
    IMAGE_CHUNKS_PATH = "image_chunks"
    COUNTRY_CHUNKS_PATH = "country_chunks"

    KEYWORDS = ["not classified by size of holding", "Main Results"]

    COUNTRIES = [
        #1950
        "Aden Protectorate", "Alaska", "American Samoa", "Australia", "Austria",
        "Bahamas", "Barbados", "Bechuanaland Protectorate", "Belgium", "Bermuda",  
        "Brunei (British Borneo)", "North Borneo(British Borneo)", "Sarawak(British Borneo)",
        "British Guiana", "British Honduras", "British Solomon Islands", "British Somaliland",
        "Canada", "Cook and Niue Islands", "Costa Rica", "Cyprus", "Denmark", "Dominican Republic",
        "EL Salvador", "Falkland Islands", "Fiji", "Finland", "Gambia", "Germany, Federal Republic of",
        "Gilbert and Ellice Islands", "Gold Coast and British Togoland",
        
        "Guam", "Guatemala", "Hawaii", "Honduras", "Hungary", "Iraq", "Ireland", "Israel(Jewish Sector)",
        "Israel(Arabs, Druzes and other Minority Groups Sector)", "Jamaica", "Japan", "Kenya", "Leeward Islands",
        "Luxembourg", "Malaya, Federation of", "Malta and Gozo", "Mauritius", "Netherlands", "New Hebrides",
        "New Zealand", "Nigeria and British Cameroons", "Northern Rhodesia(African Agriculture)",
        "Northern Rhodesia(European Holdings)", "Norway", "Nyasaland", "Philippines", "Portugal", "Puerto Rico",
        "Ryukyu Islands", "Saar, the", "Saint Helena", "Seychelles", "Sierra Leone", "Singapore Island",
        "Southern Rhodesia (African Agriculture)", "Southern Rhodesia (European Holdings)", "Swaziland",
        "Sweden", "Switzerland", "Tonga", "Trinidad and Tobago", "Uganda", "Union of South Africa",
        "United Kingdom(Great Britain )", "United Kingdom(Northern Ireland)", "United States of America",
        "Uruguay", "Virgin Islands", "Western Samoa", "Windward Islands", "Yugoslavia", "Zanzibar and Pemba",

        #1960
        "Argentina", "Colombia", "China (Taiwan)", "Ceylon", "Central African Republic",
        "Italy", "Indonesia Farm household", "Indonesia Estates", "Iran", "Kenya African holdings", "Korea, Republic of",
        "Lebanon", "Lesotho", "Libya", "Mexico", "Madagascar", "Mali", "Malaysia Estates", "Malaysia Government farms",
        "Nicaragua", "Peru", "Pakistan", "East Pakistan", "Panama", "Paraguay", "Poland", "Portuguese Guinea",
        "Spain", "Senegal", "South West Africa", "Surinam", "Tanganyika", "Thailand", "Tunisia", "Turkey", "United Arab Republic", 
        "Venezuela", "Viet-Nam, Republic of",

        #1930
        "Algeria", "Czechoslovakia", "Commonwealth of Australia", "Chile", "Egypt",
        "England and Wales", "Estonia", "France", "French West Africa", "Greece",
        "India", "Irish Free State","Latvia", "Lithuania", "Mauritius", "Outlying Territories and Possessions of the United States", 
        "Mozambique", "Switzerland", "Scotland",
        ]

    YEARS = [1930, 1950, 1960]

    @classmethod
    def initialize(cls):
        os.makedirs(cls.OUTPUT_PATH, exist_ok=True)
        os.makedirs(cls.IMAGE_CHUNKS_PATH, exist_ok=True)
        os.makedirs(cls.COUNTRY_CHUNKS_PATH, exist_ok=True) 