<div align="center">
  <h1>
    Datu Core
  </h1>

  <h2>
    LLM-Driven Data Transformations.
  </h2>

  <div align="center">
    <a href="https://github.com/Datuanalytics/datu-core/graphs/commit-activity"><img alt="GitHub commit activity" src="https://img.shields.io/github/commit-activity/m/Datuanalytics/datu-core"/></a>
    <a href="https://github.com/Datuanalytics/datu-core/issues"><img alt="GitHub open issues" src="https://img.shields.io/github/issues/Datuanalytics/datu-core"/></a>
    <a href="https://github.com/Datuanalytics/datu-core/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/Datuanalytics/datu-core"/></a>
    <a href="https://github.com/Datuanalytics/datu-core/pulls"><img alt="GitHub open pull requests" src="https://img.shields.io/github/issues-pr/Datuanalytics/datu-core"/></a>
    <a href="https://pypi.org/project/datu-core/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/datu-core"/></a>
    <a href="https://python.org"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/datu-core"/></a>
  </div>
  
  <p>
    <a href="https://docs.datu.fi/">Documentation</a>
  </p>
</div>

- [LLM-Driven Data Transformations](#llm-driven-data-transformations)
- [Installation](#installation)
- [Running the application](#running-the-application)
  - [Connect to datasource](#connect-to-datasource)
  - [Configurable parameters](#configurable-parameters)
  - [Features](#features)
  - [Documentation](#documentation)
  - [Contributing ❤️](#contributing-️)
  - [Ready to scale?](#ready-to-scale)
  - [License](#license)

# LLM-Driven Data Transformations

Datu is an AI-powered analyst agent that lets you model, visualize, analyze, and act on your data in minutes, all in plain English without technical expertise required. You can connect Datu Analyst to a variety of tools or MCP servers to perform tasks typically done by data analysts or data scientists. AI Analyst can do:  

- Connect to your data platform  

- Identify data quality issues  

- Identify and model data based on user request  

- Visualise and analyse data to understand "why" behind KPIs  

# Installation

Ensure you have installed Python 3.11+.

```sh
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

#Install datu core
pip install 'datu-core[all]'

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
  Automatically introspects the target database schema and caches the discovered metadata.

- **LLM Integration for SQL Generation:**  
  Uses OpenAI's API (e.g., GPT-4o-mini) to generate SQL queries that transform raw (Silver) data into a Gold layer format. The system prompt includes a concise summary of the schema to help the LLM generate valid queries.

- **Transformation Preview:**  
  The generated SQL is previewed by executing a sample query (with a LIMIT) and displaying the result in a formatted HTML table.

- **Persistent View Creation:**  
  Users can review the transformation preview and then create a view in the Gold layer. This view automatically reflects updates from the underlying Bronze data.

- **CSV Download:**  
  Users can download the full result of the transformation as a CSV file.

- **User-Friendly Chat Interface:**  
  The frontend features a ChatGPT-like interface with persistent conversation state, syntax highlighting for code blocks, and copy-to-clipboard functionality.

- **CSV Upload:**
  Upload data as CSV files, in addition to or instead of connecting to a database. 


- **Visualizations:** 
  Create bar, line, area, scatter, pie, or KPI visualizations to explore your data. 

- **Data Catalog:**  
  View automatically generated business definitions for your fields. 

- **Dashboards:**
  Build dashboards with multiple KPIs to share insights with stakeholders. 


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

## Ready to scale?

If you are looking for Datu SaaS then [Talk to us](hello@datu.fi)

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
