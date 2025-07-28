#!/bin/bash

set -e 

echo "🔧 Creating schema and loading CSVs..."
/load_csvs.sh
echo "✅ CSV load completed."