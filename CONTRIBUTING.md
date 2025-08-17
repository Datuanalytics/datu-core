- [Contributing Guidelines](#contributing-guidelines)
  - [Reporting Bugs/Feature Requests](#reporting-bugsfeature-requests)
  - [Developer experience](#developer-experience)
    - [Pre-requisites](#pre-requisites)
      - [Install uv](#install-uv)
      - [VSCode setup](#vscode-setup)
    - [Code quality checks](#code-quality-checks)
    - [Code Formatting and Style Guidelines](#code-formatting-and-style-guidelines)
  - [Contributing via Forking the repository and  Pull Requests](#contributing-via-forking-the-repository-and--pull-requests)
  - [Finding contributions to work on](#finding-contributions-to-work-on)
    - [How to run the application?](#how-to-run-the-application)
          - [Start application](#start-application)
          - [Stop application](#stop-application)
    - [How to add datasources](#how-to-add-datasources)
      - [Postgres](#postgres)
      - [Sqlserver](#sqlserver)
    - [Frontend Build \& Deployment](#frontend-build--deployment)
    - [Frontend Testing](#frontend-testing)
      - [Running Tests](#running-tests)
  - [Releasing a version](#releasing-a-version)
    - [Bump package version](#bump-package-version)
    - [Update changelog](#update-changelog)

# Contributing Guidelines

Thank you for your interest in contributing to our project. Whether it's a bug report, new feature, correction, or additional
documentation, we greatly value feedback and contributions from our community.

Please read through this document before submitting any issues or pull requests to ensure we have all the necessary
information to effectively respond to your bug report or contribution.

## Reporting Bugs/Feature Requests

We welcome you to use the [Bug Reports](../../issues/new?template=bug_report.yml) file to report bugs or [Feature Requests](../../issues/new?template=feature_request.yml) to suggest features.

For a list of known bugs and feature requests:
- Check [Bug Reports](../../issues?q=is%3Aissue%20state%3Aopen%20label%3Abug) for currently tracked issues
- See [Feature Requests](../../issues?q=is%3Aissue%20state%3Aopen%20label%3Aenhancement) for requested enhancements

When filing an issue, please check for already tracked items

Please try to include as much information as you can. Details like these are incredibly useful:

* A reproducible test case or series of steps
* The version of our code being used (commit ID)
* Any modifications you've made relevant to the bug
* Anything unusual about your environment or deployment


## Developer experience


### Pre-requisites
#### Install uv

[uv](https://docs.astral.sh/uv/) will manage python versions and dependency management for this application. [hatch](https://hatch.pypa.io/1.13/) is used for building and dynamic version management.
 
- Install [uv](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)
- Install [hatch](https://hatch.pypa.io/1.13/install/)
- Managing [dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/)
```sh
uv venv .venv # create a virtual environment
source .venv/bin/activate # activate .venv, on Windows: venv\Scripts\activate
uv sync --all-groups --all-extras # sync packages
```
- Minimum python requirement for this application is 3.11

#### VSCode setup

- Format
- Lint
- Test (with explorer)
- Run and debug
- Extension suggestions

We will be using [ruff](https://docs.astral.sh/ruff/).

- Use below settings.json after installing Ruff extension in vscode

```json
{
    "[python]": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit",
    },
    },
    "notebook.formatOnSave.enabled": true,
    "notebook.codeActionsOnSave": {
    "notebook.source.organizeImports": "explicit",
  }
}
```

- Use below extensions with VSCode to make your development faster and automated formatting.
```json
{
    "recommendations": [
        "njpwerner.autodocstring",
        "littlefoxteam.vscode-python-test-adapter",
        "charliermarsh.ruff",
        "ms-python.vscode-pylance",
        "tamasfe.even-better-toml",
        "yzhang.markdown-all-in-one",
        "bierner.markdown-mermaid",
        "ms-python.mypy-type-checker"
    ]
}
```

### Code quality checks 

### Code Formatting and Style Guidelines

We use the following tools to ensure code quality:
1. **ruff** - For formatting and linting
2. **mypy** - For static type checking

These tools are configured in the [pyproject.toml](./pyproject.toml) file. Please ensure your code passes all linting and type checks before submitting a pull request:

It is developers duty to make sure the the code adhers to quality checks imposed by the maintainers. 

Make sure you virtual environment is upto date with all groups especially with dev

```sh
uv sync --all-groups --all-extras # recommended for developement
uv sync --dev # just syncing dev
```

Install precommit hooks

```sh
task install-quality-check # One time activity until there is a change in .pre-commit-config.yaml
```
```sh
task quality-check # check if there are errors and fix them!
```

## Contributing via Forking the repository and  Pull Requests

All contributions to Datu need to start on a [fork of the repository](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo). Once you have successfully forked the Datu core repo, clone a local version to your machine:

```sh
git clone https://github.com/GITHUB-USERNAME/prefect.git
cd datu-core
```

Create a branch with an informative name:

```sh
git checkout -b fix-for-issue-NUM
```

After committing your changes to this branch, you can then open a pull request from your fork that we will review with you.

To send us a pull request, please:

1. Format your code using `hatch fmt --formatter`.
2. Run linting checks with `hatch fmt --linter`.
3. Ensure local tests pass with `hatch test`.
4. Commit to your branch using clear commit messages following the [Conventional Commits](https://www.conventionalcommits.org) specification.
5. Include your change in the changelog using towncrier which is configured using pyproject.toml.
6. Pay attention to any automated CI failures reported in the pull request, and stay involved in the conversation.

## Finding contributions to work on
Looking at the existing issues is a great way to find something to contribute to.

You can check:
- Our known bugs list in [Bug Reports](../../issues?q=is%3Aissue%20state%3Aopen%20label%3Abug) for issues that need fixing
- Feature requests in [Feature Requests](../../issues?q=is%3Aissue%20state%3Aopen%20label%3Aenhancement) for new functionality to implement

### How to run the application?

As developers are using multiple OS, most of the common functionalities are wired in [task](https://taskfile.dev/).

- Install [task](https://taskfile.dev/installation/)
- Install [docker](https://docs.docker.com/engine/install/)

Create a .env file. Use .env.docker as sample and in addition remember to add then set DATU_OPENAI_API_KEY. In this set up , datu and postgres are running in docker container.

###### Start application
Below command will use the data from demo folder and start the services for demo and development.

```sh
task server-container-start
```

###### Stop application

```sh
task server-container-stop
```

### How to add datasources

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
      dbname: my_sap_bronze
      schema: bronze
    dev-sqlserver:
      type: sqlserver
      driver: 'ODBC Driver 18 for SQL Server' # Mandatory for sqlserver.
      host: localhost
      port: 1433
      user: sa
      password: Password123!
      dbname: my_sap_bronze
      schema: bronze
```

#### Postgres

By default application uses postgres as the datasource. 

#### Sqlserver

For sqlserver to work you have to make sure the below ODBC driver is installed on your machine according to the Operating System.  

(Install ODBC driver)[https://learn.microsoft.com/en-us/sql/connect/python/pyodbc/step-1-configure-development-environment-for-pyodbc-python-development?view=sql-server-ver16&tabs=windows]

If you would like to use the local sqlserver make sure to start sqlserver with below command.

```sh
task sqlserver-start
```

### Frontend Build & Deployment

**Pre-requisites**

Node.js & npm: Ensure you have Node.js (v14 or later) and npm installed.
**Setup**

  Navigate to the frontend folder:

```bash
cd frontend
```
Install dependencies:
```bash
npm install
```

**Production Build**

Build the Production Bundle:

To create an optimized production build, run in the frontend folder:

```bash
npm run build
```

This command compiles the application into a build folder. The output is optimized for best performance and can be served using any static file server or integrated with the backend server.

### Frontend Testing

The frontend tests use the following frameworks and libraries:
- **Jest**: A JavaScript testing framework.
- **React Testing Library**: A library for testing React components.

All required dependencies are listed in the `package.json` file. To ensure everything is installed, run:

```sh
npm install
```

#### Running Tests

To run all frontend tests, navigate to the project root and execute:

```sh
npx jest --config tests/jest.config.js --verbose
```

Debugging Tests
To debug tests, you can use the --debug flag:
```sh
npx jest --config tests/jest.config.js --verbose --debug
```

Clearing Jest Cache
If you encounter issues with stale data, clear Jest's cache using:

```sh
npx jest --clearCache
```
## Releasing a version
### Bump package version 

- Run below script to update the version of the package. we will be using [semver](https://semver.org/) scheme.

```sh
hatch version # this will give you a version for local.
```

we have enabled the dynamic versioning using hatch-vcs and follows the github releases.

### Update changelog

- We are using [towncrier](https://towncrier.readthedocs.io/en/stable/tutorial.html) to keep the changelogs

The integrations are already done and you may use with below commands.

```sh
towncrier create -c "Basic LLM and postgres integrations" # use your message and follow the prompts. This is something you can do every time even if you are not doing any release.
```

```sh
task draft-changelog # To see the change logs without making changes in the changelog
```

```sh
task release-changelog # To release notes for the current version
```


Once the changelog are in place then go ahead and merge the PR to main. Once its in the main branch then do a git release.
