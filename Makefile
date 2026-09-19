
.PHONY: help up down restart build rebuild ps \
	logs logs-auth logs-products logs-reviews logs-consumer logs-analytics logs-analytics-consumer logs-notification \
	logs-gateway logs-auth-postgres logs-products-postgres logs-reviews-postgres logs-analytics-postgres \
	logs-auth-redis logs-products-redis logs-rabbitmq logs-elasticsearch \
	logs-grafana logs-prometheus logs-mailhog logs-adminer logs-redis-monitoring \
	logs-elasticvue \
	sh-auth sh-products sh-reviews sh-consumer sh-analytics sh-analytics-consumer sh-notification \
	psql-auth psql-products psql-reviews psql-analytics \
	redis-auth redis-products \
	migrate-auth migrate-products migrate-reviews migrate-analytics \
	migrate-create-auth migrate-create-products migrate-create-reviews migrate-create-analytics \
	ruff-auth ruff-products ruff-reviews ruff-analytics ruff-all \
	mypy-auth mypy-products mypy-reviews mypy-analytics mypy-all \
	lint-auth lint-products lint-reviews lint-analytics lint-all \
	up-auth up-products up-reviews up-analytics up-notification \
	down-auth down-products down-reviews down-analytics down-notification \
	restart-auth restart-products restart-reviews restart-analytics restart-notification \
	restart-infra

COMPOSE = docker compose

AUTH = auth-backend
PRODUCTS = products-backend
REVIEWS = reviews-backend
CONSUMER = reviews-consumer
ANALYTICS = analytics-backend
ANALYTICS_CONSUMER = analytics-consumer
NOTIFICATION = notification-service

AUTH_DB = auth-postgres
PRODUCTS_DB = products-postgres
REVIEWS_DB = reviews-postgres
ANALYTICS_DB = analytics-postgres

AUTH_REDIS = auth-redis
PRODUCTS_REDIS = products-redis


help:
	@echo "Docker:"
	@echo "  make up                 - запустить всё"
	@echo "  make down               - остановить всё"
	@echo "  make restart            - перезапустить всё"
	@echo "  make build              - собрать образы"
	@echo "  make rebuild            - пересобрать без cache"
	@echo "  make ps                 - статус контейнеров"
	@echo ""
	@echo "Логи:"
	@echo "  make logs               - логи всех контейнеров"
	@echo "  make logs-auth          - auth-backend"
	@echo "  make logs-products      - products-backend"
	@echo "  make logs-reviews       - reviews-backend"
	@echo "  make logs-consumer      - reviews-consumer"
	@echo "  make logs-analytics     - analytics-backend"
	@echo "  make logs-analytics-consumer - analytics-consumer"
	@echo "  make logs-notification  - notification-service"
	@echo "  make logs-gateway       - api-gateway"
	@echo "  make logs-auth-postgres"
	@echo "  make logs-products-postgres"
	@echo "  make logs-reviews-postgres"
	@echo "  make logs-analytics-postgres"
	@echo "  make logs-auth-redis"
	@echo "  make logs-products-redis"
	@echo "  make logs-rabbitmq"
	@echo "  make logs-elasticsearch"
	@echo "  make logs-prometheus"
	@echo "  make logs-grafana"
	@echo "  make logs-mailhog"
	@echo "  make logs-adminer"
	@echo "  make logs-redis-monitoring"
	@echo "  make logs-elasticvue"
	@echo ""
	@echo "Shell:"
	@echo "  make sh-auth"
	@echo "  make sh-products"
	@echo "  make sh-reviews"
	@echo "  make sh-consumer"
	@echo "  make sh-analytics"
	@echo "  make sh-analytics-consumer"
	@echo "  make sh-notification"
	@echo ""
	@echo "PostgreSQL:"
	@echo "  make psql-auth"
	@echo "  make psql-products"
	@echo "  make psql-reviews"
	@echo "  make psql-analytics"
	@echo ""
	@echo "Redis:"
	@echo "  make redis-auth"
	@echo "  make redis-products"
	@echo ""
	@echo "Alembic:"
	@echo "  make migrate-auth"
	@echo "  make migrate-products"
	@echo "  make migrate-reviews"
	@echo "  make migrate-analytics"
	@echo "  make migrate-create-auth"
	@echo "  make migrate-create-products"
	@echo "  make migrate-create-reviews"
	@echo "  make migrate-create-analytics"
	@echo ""
	@echo "Проверки:"
	@echo "  make ruff-all"
	@echo "  make mypy-all"
	@echo "  make lint-all"


# Docker

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

build:
	$(COMPOSE) build

rebuild:
	$(COMPOSE) build --no-cache

ps:
	$(COMPOSE) ps


# Logs

logs:
	$(COMPOSE) logs -f

logs-auth:
	$(COMPOSE) logs -f $(AUTH)

logs-products:
	$(COMPOSE) logs -f $(PRODUCTS)

logs-reviews:
	$(COMPOSE) logs -f $(REVIEWS)

logs-consumer:
	$(COMPOSE) logs -f $(CONSUMER)

logs-analytics:
	$(COMPOSE) logs -f $(ANALYTICS)

logs-analytics-consumer:
	$(COMPOSE) logs -f $(ANALYTICS_CONSUMER)

logs-notification:
	$(COMPOSE) logs -f $(NOTIFICATION)

logs-gateway:
	$(COMPOSE) logs -f api-gateway

logs-auth-postgres:
	$(COMPOSE) logs -f $(AUTH_DB)

logs-products-postgres:
	$(COMPOSE) logs -f $(PRODUCTS_DB)

logs-reviews-postgres:
	$(COMPOSE) logs -f $(REVIEWS_DB)

logs-analytics-postgres:
	$(COMPOSE) logs -f $(ANALYTICS_DB)

logs-auth-redis:
	$(COMPOSE) logs -f $(AUTH_REDIS)

logs-products-redis:
	$(COMPOSE) logs -f $(PRODUCTS_REDIS)

logs-rabbitmq:
	$(COMPOSE) logs -f rabbitmq

logs-elasticsearch:
	$(COMPOSE) logs -f elasticsearch

logs-prometheus:
	$(COMPOSE) logs -f prometheus

logs-grafana:
	$(COMPOSE) logs -f grafana

logs-mailhog:
	$(COMPOSE) logs -f mailhog

logs-adminer:
	$(COMPOSE) logs -f adminer

logs-redis-monitoring:
	$(COMPOSE) logs -f redis_monitoring

logs-elasticvue:
	$(COMPOSE) logs -f elasticvue


# Shell

sh-auth:
	$(COMPOSE) exec $(AUTH) sh

sh-products:
	$(COMPOSE) exec $(PRODUCTS) sh

sh-reviews:
	$(COMPOSE) exec $(REVIEWS) sh

sh-consumer:
	$(COMPOSE) exec $(CONSUMER) sh

sh-analytics:
	$(COMPOSE) exec $(ANALYTICS) sh

sh-analytics-consumer:
	$(COMPOSE) exec $(ANALYTICS_CONSUMER) sh

sh-notification:
	$(COMPOSE) exec $(NOTIFICATION) sh


# PostgreSQL

psql-auth:
	$(COMPOSE) exec $(AUTH_DB) sh -c 'PGPASSWORD="$$POSTGRES_PASSWORD" psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

psql-products:
	$(COMPOSE) exec $(PRODUCTS_DB) sh -c 'PGPASSWORD="$$POSTGRES_PASSWORD" psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

psql-reviews:
	$(COMPOSE) exec $(REVIEWS_DB) sh -c 'PGPASSWORD="$$POSTGRES_PASSWORD" psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

psql-analytics:
	$(COMPOSE) exec $(ANALYTICS_DB) sh -c 'PGPASSWORD="$$POSTGRES_PASSWORD" psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'


# Redis

redis-auth:
	$(COMPOSE) exec $(AUTH_REDIS) sh -c 'redis-cli --no-auth-warning -a "$$REDIS_PASSWORD"'

redis-products:
	$(COMPOSE) exec $(PRODUCTS_REDIS) sh -c 'redis-cli --no-auth-warning -a "$$REDIS_PASSWORD"'


# Alembic

migrate-auth:
	$(COMPOSE) exec $(AUTH) alembic upgrade head

migrate-products:
	$(COMPOSE) exec $(PRODUCTS) alembic upgrade head

migrate-reviews:
	$(COMPOSE) exec $(REVIEWS) alembic upgrade head

migrate-analytics:
	$(COMPOSE) exec $(ANALYTICS) alembic upgrade head


migrate-create-auth:
	@read -p "Migration message: " message; \
	$(COMPOSE) exec $(AUTH) \
	alembic revision --autogenerate -m "$$message"

migrate-create-products:
	@read -p "Migration message: " message; \
	$(COMPOSE) exec $(PRODUCTS) \
	alembic revision --autogenerate -m "$$message"

migrate-create-reviews:
	@read -p "Migration message: " message; \
	$(COMPOSE) exec $(REVIEWS) \
	alembic revision --autogenerate -m "$$message"

migrate-create-analytics:
	@read -p "Migration message: " message; \
	$(COMPOSE) exec $(ANALYTICS) \
	alembic revision --autogenerate -m "$$message"


# Ruff

ruff-auth:
	$(COMPOSE) exec $(AUTH) ruff check .

ruff-products:
	$(COMPOSE) exec $(PRODUCTS) ruff check .

ruff-reviews:
	$(COMPOSE) exec $(REVIEWS) ruff check .

ruff-analytics:
	$(COMPOSE) exec $(ANALYTICS) ruff check .

ruff-notification:
	$(COMPOSE) exec $(NOTIFICATION) ruff check .

ruff-all:
	$(COMPOSE) exec $(AUTH) ruff check .
	$(COMPOSE) exec $(PRODUCTS) ruff check .
	$(COMPOSE) exec $(REVIEWS) ruff check .
	$(COMPOSE) exec $(ANALYTICS) ruff check .
	$(COMPOSE) exec $(NOTIFICATION) ruff check .


# Mypy

mypy-auth:
	$(COMPOSE) exec $(AUTH) mypy .

mypy-products:
	$(COMPOSE) exec $(PRODUCTS) mypy .

mypy-reviews:
	$(COMPOSE) exec $(REVIEWS) mypy .

mypy-analytics:
	$(COMPOSE) exec $(ANALYTICS) mypy .

mypy-notification:
	$(COMPOSE) exec $(NOTIFICATION) mypy .

mypy-all:
	$(COMPOSE) exec $(AUTH) mypy .
	$(COMPOSE) exec $(PRODUCTS) mypy .
	$(COMPOSE) exec $(REVIEWS) mypy .
	$(COMPOSE) exec $(ANALYTICS) mypy .
	$(COMPOSE) exec $(NOTIFICATION) mypy .


# Ruff + mypy

lint-auth:
	$(MAKE) ruff-auth
	$(MAKE) mypy-auth

lint-products:
	$(MAKE) ruff-products
	$(MAKE) mypy-products

lint-reviews:
	$(MAKE) ruff-reviews
	$(MAKE) mypy-reviews

lint-analytics:
	$(MAKE) ruff-analytics
	$(MAKE) mypy-analytics

lint-notification:
	$(MAKE) ruff-notification
	$(MAKE) mypy-notification

lint-all:
	$(MAKE) ruff-all
	$(MAKE) mypy-all


# Individual services

up-auth:
	$(COMPOSE) up -d auth-backend

up-products:
	$(COMPOSE) up -d products-backend

up-reviews:
	$(COMPOSE) up -d reviews-backend

up-analytics:
	$(COMPOSE) up -d analytics-backend

up-notification:
	$(COMPOSE) up -d notification-service


down-auth:
	$(COMPOSE) stop auth-backend

down-products:
	$(COMPOSE) stop products-backend

down-reviews:
	$(COMPOSE) stop reviews-backend

down-analytics:
	$(COMPOSE) stop analytics-backend

down-notification:
	$(COMPOSE) stop notification-service


restart-auth:
	$(COMPOSE) restart auth-backend

restart-products:
	$(COMPOSE) restart products-backend

restart-reviews:
	$(COMPOSE) restart reviews-backend

restart-analytics:
	$(COMPOSE) restart analytics-backend

restart-notification:
	$(COMPOSE) restart notification-service


# Infrastructure

restart-infra:
	$(COMPOSE) restart \
		auth-postgres \
		products-postgres \
		reviews-postgres \
		analytics-postgres \
		auth-redis \
		products-redis \
		rabbitmq \
		elasticsearch
