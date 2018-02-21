FROM openjdk:8u151-jre

RUN cd /bin/ && wget https://github.com/remind101/ssm-env/releases/download/v0.0.2/ssm-env && chmod +x ssm-env

COPY build/libs/*.jar /app.jar

ENV JAVA_OPTS=""
ENV JAVA_MEMORY_OPTS="-XX:+UnlockExperimentalVMOptions -XX:+UseCGroupMemoryLimitForHeap -XX:+UseG1GC -XX:MaxRAMFraction=2 -XshowSettings:vm"

CMD ["ssm-env", "-with-decryption", "sh", "-c", "java $JAVA_OPTS $JAVA_MEMORY_OPTS -jar /app.jar"]
