FROM nginx:1.21-alpine

RUN rm /etc/nginx/conf.d/default.conf /etc/nginx/nginx.conf
COPY setting.nginx /etc/nginx/nginx.conf
COPY site.nginx /etc/nginx/conf.d/site.conf