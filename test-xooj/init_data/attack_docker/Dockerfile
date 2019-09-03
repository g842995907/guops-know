FROM ubuntu:16.04

RUN apt-get update && apt-get install -y openssh-server
RUN mkdir /var/run/sshd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

RUN mkdir /home/attack


RUN apt install -y vim
RUN apt install -y python
RUN apt install -y python-pip

ENV proxy_pip='--trusted-host mirrors.aliyun.com -i http://mirrors.aliyun.com/pypi/simple/'
RUN pip install --upgrade pip $proxy_pip
RUN pip install pwntools scapy zio $proxy_pip

COPY run_attack.sh /home/
COPY ./attack /home/attack

#ENTRYPOINT service ssh start && bash
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]