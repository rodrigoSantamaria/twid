docker build . -t twid-soa-resources

docker run -d --rm --name container_twid-soa-resources -p 8000:8000 twid-soa-resources