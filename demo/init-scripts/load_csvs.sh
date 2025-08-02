#!/bin/bash

SCHEMA="bronze"  # Set target schema

psql -U $POSTGRES_USER -d $POSTGRES_DB -c "CREATE SCHEMA IF NOT EXISTS \"$SCHEMA\";"

infer_column_types() {
  local csv_file="$1"
  local delimiter="$2"
  
  headers=$(head -n 1 "$csv_file" | sed 's/^\xEF\xBB\xBF//')  # Remove BOM
  columns=($(echo "$headers" | tr "$delimiter" "\n"))

  types=()
  mapfile -t lines < <(head -n 11 "$csv_file")  # header + 10 rows

  for ((i=0; i<${#columns[@]}; i++)); do        
    col_upper=$(echo "${columns[i]}" | tr '[:lower:]' '[:upper:]')
    type="VARCHAR"
    is_numeric=true

    for ((j=1; j<${#lines[@]}; j++)); do
      IFS="$delimiter" read -ra fields <<< "${lines[j]}"
      val="${fields[i]}"
      [[ -z "$val" ]] && continue

      if [[ "$col_upper" =~ (POSTAL|PHONE|CODE|ID) ]]; then
        is_numeric=false
        type="VARCHAR"
        break

      elif [[ "$col_upper" =~ (DATE|CREATED|UPDATED) ]]; then
          is_numeric=false          
          if [[ "$val" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ || "$val" =~ ^[0-9]{8}$ ]]; then       
            type="DATE"  
            break
          else
            type="VARCHAR"      
            break                   
          fi    

      elif ! [[ "$val" =~ ^[0-9]+$ ]]; then
        is_numeric=false
        break
      fi
    done

    if [[ "$type" == "VARCHAR" && "$is_numeric" == true ]]; then
      type="NUMERIC"
    fi

    types+=("$type")                            
  done

  # Combine columns and types into a CREATE TABLE statement with quoted column names
  create_statement=""
  for i in "${!columns[@]}"; do
    create_statement+="\"${columns[$i]}\" ${types[$i]}"  # Quote the column names
    if [[ $i -lt $((${#columns[@]} - 1)) ]]; then
      create_statement+=", "
    fi
  done
  echo "$create_statement"
}

for csv_file in /csvs/*.csv; do
  table_name=$(basename "$csv_file" .csv)
  echo "Processing $csv_file"

  table_exists=$(psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = '$SCHEMA' AND table_name = '$table_name');" | tr -d '[:space:]')
  
  if [[ "$table_exists" == "f" ]]; then
    echo "Table $SCHEMA.$table_name does not exist. Creating table..."

    create_table_statement=$(infer_column_types "$csv_file" ",")  
    psql -U $POSTGRES_USER -d $POSTGRES_DB -c "CREATE TABLE \"$SCHEMA\".\"$table_name\" ($create_table_statement);"
  fi

  echo "Loading $csv_file into $SCHEMA.$table_name"
  # Clean the BOM from the CSV file before loading
  sed '1s/^\xEF\xBB\xBF//' "$csv_file" | psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\copy \"$SCHEMA\".\"$table_name\" FROM stdin DELIMITER ',' CSV HEADER;"
done
