docker build . -t twid-soa-control

docker run -d --rm --name container_twid-soa-control -p 8001:8001 twid-soa-control