## celery基础介绍

任务队列是一种跨线程、跨机器工作的一种机制.

  任务队列中包含称作任务的工作单元。有专门的工作进程持续不断的监视任务队列，并从中获得新的任务并处理.

  celery通过消息进行通信，通常使用一个叫Broker(中间人)来协client(任务的发出者)和worker(任务的处理者). clients发出消息到队列中，broker将队列中的信息派发给worker来处理。

(celery客户端向borker里面发送消息, borker将队列里的信息发送给worker处理 这边的客户端可能的就是一个hash值 在celery app里面创建的celery的任务名字 发送给worker worker拿到名字去处理定义的任务函数)

  一个celery系统可以包含很多的worker和broker，可增强横向扩展性和高可用性能。

### 使用

​	使用celery第一件要做的最为重要的事情是需要先创建一个Celery实例，我们一般叫做celery应用，或者更简单直接叫做一个app。app应用是我们使用celery所有功能的入口，比如创建任务，管理任务等，在使用celery的时候，app必须能够被其他的模块导入。