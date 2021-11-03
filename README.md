# capts

## Deployment

### Prod

```
cd docker-compose
cp envs/prod .env
DOCKER_BUILDKIT=1 docker-compose -f prod.env up
```
