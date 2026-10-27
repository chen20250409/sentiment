#!/usr/bin/env bash
# 日常运维脚本：在项目根目录执行 ./deploy/ops.sh <命令>
set -e
cd "$(dirname "$0")/.."

case "$1" in
  start)
    docker compose up -d --build
    ;;
  stop)
    docker compose down
    ;;
  restart)
    docker compose restart api
    ;;
  logs)
    docker compose logs -f --tail=100 api
    ;;
  update)
    docker compose up -d --build
    ;;
  backup)
    mkdir -p .runtime
    docker compose exec -T mysql sh -c 'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" sentiment' \
      > ".runtime/backup_$(date +%Y%m%d_%H%M%S).sql"
    echo "backup written to .runtime/"
    ;;
  *)
    echo "usage: ./deploy/ops.sh start|stop|restart|logs|update|backup"
    exit 1
    ;;
esac
