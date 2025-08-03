- [LLM-Driven Data Transformations](#llm-driven-data-transformations)
- [Installation](#installation)
- [Running the application](#running-the-application)
  - [Connect to datasource](#connect-to-datasource)
  - [Configurable parameters](#configurable-parameters)
  - [Features](#features)
  - [Documentation](#documentation)
  - [Contributing ❤️](#contributing-️)
  - [License](#license)

# LLM-Driven Data Transformations

This application is a FastAPI-based system that leverages a Large Language Model (LLM) to generate SQL transformation queries from natural language business requirements. Its primary purpose is to transform data from the Bronze layer into a Gold layer representation by creating persistent database views. The application now supports both cloud-based (OpenAI) and on-premises LLMs for SQL generation.

# Installation

Ensure you have installed Python 3.10+.

```sh
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

#Install datu core
pip install datu-core

```

# Running the application

```sh
# To run application type 
datu
```

## Connect to datasource

As per the current design the application will fetch all the schema that is listed in the profiles.yml. It is to avoid fetching the schema every single time.But it will only work on the **target** datasource that is selected.

**Structure of profiles.yml**

```sh
datu_demo:
  target: dev-postgres # Target is used to select the datasource that is currently active. Change this if you would like to use a different datasource.
  outputs:
    dev-postgres:
      type: postgres
      host: "{{ env_var('DB_HOST', 'localhost') }}"  # if a environment variable is supplied that gets priority. This is useful for not hardcoding.
      port: 5432
      user: postgres
      password: postgres
      dbname: my_sap_bronz
```

## Configurable parameters

Please checkout datu [documentation](https://docs.datu.fi)

## Features

- **Dynamic Schema Discovery & Caching:**  
  Automatically introspects the target database schema, caches the discovered metadata (with an optional business glossary), and refreshes the cache if older than a configurable threshold (default: 2 days).

- **LLM Integration for SQL Generation:**  
  Uses OpenAI's API (e.g., GPT-4o-mini) to generate SQL queries that transform raw (Bronze) data into a Gold layer format. The system prompt includes a concise summary of the schema to help the LLM generate valid queries.

- **Transformation Preview:**  
  The generated SQL is previewed by executing a sample query (with a LIMIT) and displaying the result in a formatted HTML table.

- **Persistent View Creation:**  
  Users can review the transformation preview and then create a view in the Gold layer. This view automatically reflects updates from the underlying Bronze data.

- **CSV Download:**  
  Users can download the full result of the transformation as a CSV file.

- **User-Friendly Chat Interface:**  
  The frontend features a ChatGPT-like interface with persistent conversation state, syntax highlighting for code blocks, and copy-to-clipboard functionality.


## Documentation

For detailed guidance & examples, explore our documentation:

- [User Guide](https://docs.datu.fi/)

## Contributing ❤️

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details on:
- Reporting bugs & features
- Development setup
- Contributing via Pull Requests
- Code of Conduct
- Reporting of security issues

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.