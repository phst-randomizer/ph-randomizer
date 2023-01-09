#!/bin/bash

# Get list of test modules
test_modules=$(pytest tests/desmume/ --collect-only -qqq)

# Declare an empty array
declare -a moduleArr

# Iterate over pytest output, appending each .py test file to the array
while IFS= read -r line; do
    moduleArr+=("$(basename $(echo "$line" | cut -d ":" -f 1))")
done <<< "$test_modules"

# Format the bash array into a JSON array
jsonArr=$(jq --compact-output --null-input '$ARGS.positional' --args -- "${moduleArr[@]}")

# Print it to stdout in a format GitHub Actions can parse
echo $(jq -n --argjson v "$jsonArr" '{"module": $v}')
