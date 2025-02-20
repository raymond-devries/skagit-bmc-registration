# Skagit BMC Registration

---

This repository hosts the code used to run the [Skagit Alpine Club Basic Mountaineering Course sign up website](https://bmc.skagitalpineclub.com). This site uses django with Vue sprinkled in for interactivity. Stripe is used to process payments. The website is hosted through AWS Lightsail, allowing for a very affordable hosting solution. CI is handled through github actions and the website deploys with every push to production. 

Required Environment Variables:
* `DJANGO_SECRET_KEY`: Required django secret key
* `DEBUG`: Defaults to False, only set to True if you are developing locally
* `ALLOWED_HOSTS`: Sets allowed hosts as a comma separated list. e.g. `127.0.0.1,0.0.0.0`
* `DATABASE_URL`: Url for the database in accordance with the url scheme of [dj-database-url](https://github.com/jacobian/dj-database-url#url-schema)
* `DEFAULT_FROM_EMAIL`: The default email django will use to send emails
* `USE_AWS_EMAIL`: Defaults to false, set to true to use aws email.
* `EMAIL_HOST_USER`: AWS smtp host user
* `EMAIL_HOST_PASSWORD`: AWS smtp host password
* `STRIPE_API_KEY`: Stripe private API key
* `STRIPE_PUBLIC_API_KEY`: Stripe public API key
* `STRIPE_ENDPOINT_SECRET`: Stripe API endpoint secret for end point (/api/stripe_webhook/) that fulfills orders
* `SENTRY_DSN`: DSN link from sentry to track errors
* `SENTRY_SAMPLE_RATE`: A rate from 0.0-1.0. Determines what percent of transactions are tracked for performance.

### Dev Notes

To deploy with pulumi the supabase sdk will need to be generated
```shell
pulumi package add terraform-provider supabase/supabase
```

Set dev env
```shell
source set_dev_env.sh
```

Setup Postgres
```shell
docker run --name skagit-bmc -e POSTGRES_HOST_AUTH_METHOD=trust -p 5432:5432 -d postgres
```

Seeding data
```shell
python manage.py migrate && aws s3 cp s3://skagit-bmc-dev/dev-dump.json - | python manage.py loaddata --format=json -
```

#### Lambda Image Testing
Build
```shell
docker buildx build --platform linux/amd64 --provenance=false -t docker-image:test -f lambda.Dockerfile .
```

Run
```shell
docker run --platform linux/amd64 --rm -it -p 9000:8080 --env-file .env-local --name django-lambda docker-image:test "SkagitRegistration.asgi.handler"
```

Test
```shell
curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"resource": "/", "path": "/", "httpMethod": "GET", "requestContext": {}, "multiValueQueryStringParameters": null}'
```
