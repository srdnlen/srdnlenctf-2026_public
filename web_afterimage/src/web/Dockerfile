FROM php:8.2-apache

COPY src/ /var/www/html/
COPY php.ini /usr/local/etc/php/php.ini

RUN apt-get update && apt-get install -y cron

COPY cron_tmp_cleanup /etc/cron.d/cron-tmp-cleanup
RUN chmod 0644 /etc/cron.d/cron-tmp-cleanup \
    && crontab /etc/cron.d/cron-tmp-cleanup

RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html

CMD cron && apache2-foreground
