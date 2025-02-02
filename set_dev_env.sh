values=$(aws secretsmanager get-secret-value --secret-id bmc/local | jq --raw-output '.SecretString')
for s in $(echo $values | jq -r "to_entries|map(\"\(.key)=\(.value|tostring)\")|.[]" ); do
    export $s
done


