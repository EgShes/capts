# capts

## Deployment

### Weights

Download weights from [here](https://disk.yandex.ru/d/t0s_zakP8RX6yg) and put it in the project root in `weights` folder

### Prod

```
cd docker-compose
cp envs/prod .env
DOCKER_BUILDKIT=1 docker-compose -f prod.yml up
```

### Dev

```
cd docker-compose
cp envs/dev .env
DOCKER_BUILDKIT=1 docker-compose -f prod.yml -f dev.overrride.yml up
```