#!/bin/bash
export PATH=$PATH:/opt/mssql-tools/bin
SCHEMA="bronze"  # Set target schema

# Create database if it doesn't exist
/opt/mssql-tools/bin/sqlcmd -S $SQLSERVER_HOST -U $SQLSERVER_USER -P $SQLSERVER_PASS -d master -Q "IF DB_ID('$SQLSERVER_DB') IS NULL BEGIN CREATE DATABASE [$SQLSERVER_DB]; END;"

# Create schema if it doesn't exist
sqlcmd -S $SQLSERVER_HOST -U $SQLSERVER_USER -P $SQLSERVER_PASS -d $SQLSERVER_DB -Q "IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '$SCHEMA') BEGIN EXEC('CREATE SCHEMA $SCHEMA'); END;"

infer_column_types() {
  local csv_file="$1"
  local delimiter="$2"

  # Read the first line (headers) and remove BOM if present
  headers=$(head -n 1 "$csv_file" | sed 's/^\xEF\xBB\xBF//')
  columns=($(echo "$headers" | tr "$delimiter" "\n"))

  DEFAULT_TYPE="VARCHAR(255)"
  types=()
  for col in "${columns[@]}"; do
    types+=("$DEFAULT_TYPE")
  done

  # Combine columns and types into a CREATE TABLE statement with square brackets
  create_statement=""
  for i in "${!columns[@]}"; do
    create_statement+="[${columns[$i]}] ${types[$i]}"  # Use square brackets for column names
    if [[ $i -lt $((${#columns[@]} - 1)) ]]; then
      create_statement+=", "
    fi
  done
  echo "$create_statement"
}


for csv_file in /csvs/*.csv; do
  table_name=$(basename "$csv_file" .csv)
  echo "Processing $csv_file"

  # Check if table exists
  table_exists=$(sqlcmd -S $SQLSERVER_HOST -U $SQLSERVER_USER -P $SQLSERVER_PASS -d $SQLSERVER_DB \
  -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$SCHEMA' AND table_name = '$table_name'" | tr -d '\r')


  # If table does not exist, create it
  if [[ "$table_exists" == "0" ]]; then
    echo "Table $SCHEMA.$table_name does not exist. Creating table..."
    create_table_statement=$(infer_column_types "$csv_file" ",")
    echo "Generated CREATE TABLE statement: CREATE TABLE $SCHEMA.$table_name ($create_table_statement);"
    create_output=$(sqlcmd -S $SQLSERVER_HOST -U $SQLSERVER_USER -P $SQLSERVER_PASS -d $SQLSERVER_DB \
        -Q "CREATE TABLE $SCHEMA.$table_name ($create_table_statement);" 2>&1)
    echo "$create_output"
  fi

  echo "Loading $csv_file into $SCHEMA.$table_name"

  sqlcmd -S $SQLSERVER_HOST -U $SQLSERVER_USER -P $SQLSERVER_PASS -d $SQLSERVER_DB -Q "BULK INSERT $SCHEMA.$table_name FROM '$csv_file' WITH (FIELDTERMINATOR = ',', ROWTERMINATOR = '\n', FIRSTROW = 2);"


done
