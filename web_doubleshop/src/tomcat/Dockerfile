FROM tomcat:9.0-jdk11-openjdk-slim

RUN cp -r /usr/local/tomcat/webapps.dist/manager /usr/local/tomcat/webapps/manager

COPY conf/server.xml /usr/local/tomcat/conf/server.xml
COPY conf/tomcat-users.xml /usr/local/tomcat/conf/tomcat-users.xml

RUN rm -rf /usr/local/tomcat/webapps/ROOT/*
COPY src/receipt.jsp /usr/local/tomcat/webapps/ROOT/receipt.jsp
COPY src/checkout.jsp /usr/local/tomcat/webapps/ROOT/checkout.jsp

RUN mkdir -p /usr/local/tomcat/logs/receipts

RUN cp -r /usr/local/tomcat/webapps.dist/manager /usr/local/tomcat/webapps/manager
RUN mkdir -p /usr/local/tomcat/webapps/srdnlen{d0uble_m1sC0nf_aR3_n0t_fUn}

RUN groupadd -r tomcat && useradd -r -g tomcat tomcat

RUN chown -R root:tomcat /usr/local/tomcat/webapps
RUN chmod -R 550 /usr/local/tomcat/webapps

RUN chown -R tomcat:tomcat /usr/local/tomcat/temp /usr/local/tomcat/work /usr/local/tomcat/logs

USER tomcat

EXPOSE 8080
CMD ["catalina.sh", "run"]