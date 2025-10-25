# RAG Outputs Data Description

This document describes the structure and contents of the extracted agricultural indicators stored in the `data/rag_outputs/` directory.

## Overview

The `rag_outputs` directory contains structured CSV files with agricultural indicators extracted from World Census of Agriculture (WCA) reports for the period 1930-1960. The data was extracted using a RAG (Retrieval-Augmented Generation) pipeline that processes scanned PDF documents.

## Directory Structure

```
data/rag_outputs/
├── {Country}/
│   ├── output_0_{Country}_{Indicator}.csv
│   ├── output_1_{Country}_{Indicator}.csv
│   ├── ...
│   └── output_8_{Country}_{Indicator}.csv
```

## Indicator Categories

The dataset is organized into **9 categories**:

- **Category 0**: Holding and tenure
- **Category 1**: Land Utilization
- **Category 2**: Crops 
- **Category 3**: Livestock and poultry
- **Category 4**: Employment in agriculture
- **Category 5**: Farm Population
- **Category 6**: Agricultural technology
- **Category 7**: Irrigation and drainage
- **Category 8**: Fertilizers and soil dressings

## Time Period

- **Years**: 1930, 1950, 1960

## Countries

The dataset covers 130 countries: Aden Protectorate, Alaska, Algeria, American Samoa, Argentina, Australia, Austria, Bahamas, Barbados, Bechuanaland Protectorate, Belgium, Bermuda, British Guiana, British Honduras, British Solomon Islands, British Somaliland, Brunei (British Borneo), Canada, Central African Republic, Ceylon, Chile, China (Taiwan), Colombia, Commonwealth of Australia, Cook and Niue Islands, Costa Rica, Cyprus, Czechoslovakia, Denmark, Dominican Republic, East Pakistan, Egypt, El Salvador, England and Wales, Estonia, Falkland Islands, Fiji, Finland, France, French West Africa, Gambia, Germany (Federal Republic of), Gilbert and Ellice Islands, Gold Coast and British Togoland, Greece, Guam, Guatemala, Hawaii, Honduras, Hungary, India, Indonesia Estates, Indonesia Farm household, Iran, Iraq, Ireland, Irish Free State, Israel (Arabs, Druzes and other Minority Groups Sector), Israel (Jewish Sector), Italy, Jamaica, Japan, Kenya, Kenya African holdings, Korea (Republic of), Latvia, Lebanon, Leeward Islands, Lesotho, Libya, Lithuania, Luxembourg, Madagascar, Malaysia Estates, Malaysia Government farms, Mali, Malaya Federation of, Malta and Gozo, Mauritius, Mexico, Mozambique, Netherlands, New Hebrides, New Zealand, Nicaragua, Nigeria and British Cameroons, North Borneo (British Borneo), Northern Rhodesia (African Agriculture), Northern Rhodesia (European Holdings), Norway, Nyasaland, Outlying Territories and Possessions of the United States, Pakistan, Panama, Paraguay, Peru, Philippines, Poland, Portugal, Portuguese Guinea, Puerto Rico, Ryukyu Islands, Saar, Saint Helena, Sarawak (British Borneo), Scotland, Senegal, Seychelles, Sierra Leone, Singapore Island, South West Africa, Southern Rhodesia (African Agriculture), Southern Rhodesia (European Holdings), Spain, Surinam, Swaziland, Sweden, Switzerland, Tanganyika, Thailand, Tonga, Trinidad and Tobago, Tunisia, Turkey, Uganda, Union of South Africa, United Arab Republic, United Kingdom (Great Britain), United Kingdom (Northern Ireland), United States of America, Uruguay, Venezuela, Viet-Nam Republic of, Virgin Islands, Western Samoa, Windward Islands, Yugoslavia, Zanzibar and Pemba.

## Data Format

### CSV File Structure

All CSV files follow this structure:

```csv
Country,Year,Indicator,Value,Unit
```

