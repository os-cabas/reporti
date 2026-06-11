#!/bin/sh
set -e

echo "Aguardando o banco de dados..."
until python -c "
import MySQLdb, os, sys
try:
    MySQLdb.connect(
        host=os.environ.get('DB_HOST', 'db'),
        user=os.environ.get('DB_USER', 'root'),
        passwd=os.environ.get('DB_PASSWORD', ''),
        db=os.environ.get('DB_NAME', 'reporti_hom'),
        port=int(os.environ.get('DB_PORT', 3306))
    )
except Exception as e:
    print(f'DB indisponivel: {e}')
    sys.exit(1)
"; do
    echo "Banco nao disponivel, tentando novamente em 2s..."
    sleep 2
done

echo "Banco disponivel. Aplicando migrations..."
python manage.py migrate --noinput

echo "Coletando arquivos estaticos..."
python manage.py collectstatic --noinput

echo "Iniciando Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
