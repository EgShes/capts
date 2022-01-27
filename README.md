# Recognition of captchas

Supported captcha types:

- [fns](https://disk.yandex.ru/i/fefdsNdRlD9jWQ)

- [alcolicenziat](https://disk.yandex.ru/i/NjHmMHWj2Au85A)

## Deployment

### Weights

Ask for `WEIGHTS_GOOGLE_TOKEN` and define it in .env

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

### Documentation

Interactive API documentation is available at `/docs` endpoint