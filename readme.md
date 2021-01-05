# Skagit BMC Registration

---

This repository hosts the code used to run the Skagit Alpine Club Basic Mountaineering Course sign up website. This site uses django with Vue sprinkled in for interactivity. Stripe is used to process payments.

Required Environment Variables:
* `DJANGO_SECRET_KEY`: Required django secret key
* `DEBUG`: Defaults to False, only set to True if you are developing locally
* `ALLOWED_HOST`: Sets allowed host
* `DATABASE_URL`: Url for the database in accordance with the url scheme of [dj-database-url](https://github.com/jacobian/dj-database-url#url-schema)
* `STRIPE_API_KEY`: Stripe private API key
* `STRIPE_ENDPOINT_SECRET`: Stripe API endpoint secret for end point (/api/stripe_webhook/) that fulfills orders