# Escanea videos de Amazon S3 para moderaci贸n de contenido utilizando Amazon Scan Amazon Rekognition.. CDK deploy

!["Portada"](imagen/portada.png)

## Introducci贸n

Revisando arquitecturas me encontr茅 con [esta arquitectura](https://aws.amazon.com/es/blogs/machine-learning/scan-amazon-s3-buckets-for-content-moderation-using-s3-batch-and-amazon-rekognition/) s煤per genial馃槺, que crea una aplicaci贸n capaz de escanear videos alojados en Buckets de S3 y con operaciones Batch de S3 y Amazon Rekognition permite identificar el tipo de contenido que este contiene. 

Tratar con contenido a gran escala es a menudo desafiante, costoso y una operaci贸n pesada. El volumen de contenido generado por usuarios y de terceros ha aumentado sustancialmente en industrias como las redes sociales, el comercio electr贸nico, la publicidad en l铆nea y el intercambio de medios. Es posible que los clientes deseen revisar este contenido para asegurarse de que cumple con las regulaciones y el gobierno corporativo. Pero necesitan una soluci贸n para manejar la escala y la automatizaci贸n.
 

---

## Arquitectura 馃 鈿欙笍

!["Diagrama"](imagen/diagrama.png)

La arquitectura que plantea **Virgil Ennes** en su [publicaci贸n]((https://aws.amazon.com/es/blogs/machine-learning/scan-amazon-s3-buckets-for-content-moderation-using-s3-batch-and-amazon-rekognition/)), consiste en 6 partes 


1. El trabajo por Batch de S3 lee el archivo de video.
2. El trabajo por Batch de S3 invoca la funci贸n Lambda. 
3. La funci贸n Lambda invoca Amazon Rekogintion para realizar la revisi贸n de moderaci贸n de contenido en el video. 
4. La actividad se registra en Amazon CloudWatch. 
5. Las etiquetas encontradas por Amazon Rekogintion son almacenadas en una DynamoDB.
6. Amazon SNS env铆a una notificaci贸n por correo electronico. 

---
## Mi Arquitectura  馃 鈿欙笍 馃О

Para este playground le hice algunas modificaciones.

!["Diagrama_2"](imagen/diagrama_2.png)

1. Al agregar el video en el Bucket **data-bucket** este activa un [Event Notification](https://docs.aws.amazon.com/AmazonS3/latest/userguide/NotificationHowTo.html) que gatilla la Lambda_invokes_Rekognition. **Solo procesa videos en mp4, debes asegurar que sea mp4** 
2. Lambda_invokes_Rekognition invoca Amazon Rekogintion para realizar la revisi贸n de moderaci贸n de contenido en el video, con la API *getContentModeration*.
3. Una vez lista la revisi贸n del contenido Amazon Rekogintion notifica a traves de SNS a la lambda Lambda_porcess_Rekognition que esta listo el proceso.
 ***Esto lo modifique debido a que la lamnbda de la arquitectura original no finaliza hasta que Amazon Rekognition informe que el proceso es exitoso, si el video es muy largo la lambda quedar谩 a la espera por mucho tiempo lo cual no es costo efectivo.***  
4. La Lambda_porcess_Rekognition procesa los resultados de la revision de Amazon Rekognition invocando a **getContentModeration**. 
5. Las etiquetas encontradas por Amazon Rekogintion son almacenadas en una DynamoDB.
6. Amazon SNS env铆a una notificaci贸n por correo electronico.


---

## Despliegue 馃殌 馃懇馃徎鈥嶐煔?


**Para crear la aplicaci贸n debes seguir los siguientes pasos:**

### 1. Instalar CDK

Para realizar el despliegue de los recursos, debes instalar y configurar la cli (command line interface) de CDK, en este caso estamos utilizando CDK con Python.

[Instalaci贸n y configuraci贸n de CDK](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html)

[Documentaci贸n CDK para Python](https://docs.aws.amazon.com/cdk/api/latest/python/index.html)


### 2. Clonamos el repo y vamos la carpeta de nuestro proyecto. 

```bash
git clone https://github.com/elizabethfuentes12/AWS_ScanVideoS3Rekognition
cd AWS_ScanVideoS3Rekognition/ScanVideoS3Rekognition
```

### 3. Creamos e iniciamos el ambiente virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Este ambiente virtual (venv) nos permite aislar las versiones del python que vamos a utilizar como tambi茅n de librer铆as asociadas. Con esto podemos tener varios proyectos con distintas configuraciones.

### 4. Explicaci贸n del c贸digo

Esta herramienta esta desplegada en *us-east-1*, si quieres cambiar la regi贸n debes hacerlo en [scan_video_s3_rekognition.py](https://github.com/elizabethfuentes12/AWS_ScanVideoS3Rekognition/blob/main/ScanVideoS3Rekognition/scan_video_s3_rekognition/scan_video_s3_rekognition_stack.py) 

```python
REGION_NAME = 'tu_region'
```
 
Antes de iniciar debes agregar una direcci贸n de correo valida en [scan_video_s3_rekognition.py](https://github.com/elizabethfuentes12/AWS_ScanVideoS3Rekognition/blob/main/ScanVideoS3Rekognition/scan_video_s3_rekognition/scan_video_s3_rekognition_stack.py)  : 

```python
email="tucorreo@correo.com"
```

En el GitHub esta el c贸digo listo para desplegar, a continuaci贸n una breve explicaci贸n:

**Lambdas:**
+ [lambda_invokes_rekognition](https://github.com/elizabethfuentes12/AWS_ScanVideoS3Rekognition/blob/main/ScanVideoS3Rekognition/lambda_invokes_rekognition/lambda_function.py) : Lambda que invoca Amazon Rekogintion para realizar la revisi贸n de moderaci贸n de contenido en el video, con la API *getContentModeration* y subscribe al SNS Topic para que se notifique una vez termine la revisi贸n.

```bash
startModerationLabelDetection = rekognition.start_content_moderation(
            Video={'S3Object': {
                   'Bucket'  : bucket1, 
                   'Name'    : filename, }
                },
            ClientRequestToken=userIdentity,
            NotificationChannel = {
            'SNSTopicArn': SNS_REKOGNITION,
            'RoleArn': SNS_ROLE_ARN_REKOGNITION
                                },
            JobTag=userIdentity)
```

Puedes informarte m谩s sobre esta API en la documentaci贸n: 
https://docs.aws.amazon.com/cli/latest/reference/rekognition/start-content-moderation.html
https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rekognition.html#Rekognition.Client.start_content_moderation

* [lambda_process_Rekognition](https://github.com/elizabethfuentes12/AWS_ScanVideoS3Rekognition/blob/main/ScanVideoS3Rekognition/lambda_process_Rekognition/lambda_function.py) : Lambda que procesa los resultados de la revisi贸n de Amazon Rekognition invocando a **getContentModeration**, 

```bash
getContentModeration = rekognition.get_content_moderation(
              JobId  = moderationJobId,
              SortBy = 'TIMESTAMP')
```

escribe en DynamoDB

```bash 
table.put_item(
                    Item={
                        "Id": str(uuid.uuid4()),
                        'Timestamp': timestamp,
                        "Jobtag" : request["JobTag"],
                        'Confidence': str(round(conf_level, 1)),
                        'Name': name,
                        'ParentName': parent,
                        'Video': filename,
                        'Date': str(datetime.datetime.now())
                    })
```

y envi谩 el correo con SNS. 

```bash
message = client.publish(TargetArn = SNS_ARN, 
                         Message   = mailer,
                         Subject ='Amazon Rekognition Video Detection')
```

### 5. Instalamos los requerimientos para el ambiente de python 

Para que el ambiente pueda desplegarse, debemos agregar todas las librer铆as CDK necesarias en el archivo  [requirements.txt](https://github.com/elizabethfuentes12/AWS_ScanVideoS3Rekognition/blob/main/ScanVideoS3Rekognition/requirements.txt)


```zsh
pip install -r requirements.txt
```

### 6. Desplegando la aplicaci贸n

Previo al despliegue de la aplicaci贸n en AWS Cloud debemos asegurarnos que este sin errores para que no salten errores durante el despliegue, eso lo hacemos con el siguiente comando que genera un template de cloudformation con nuestra definici贸n de recursos en python.

```bash
cdk synth
```

Si hay alg煤n error en tu c贸digo este comando te indicara cual es con su ubicaci贸n.  

En el caso de estar cargando una nueva versi贸n de la aplicaci贸n puedes revisar que es lo nuevo con el siguiente comando: 

```
cdk diff
```

Procedemos a desplegar la aplicaci贸n: 

```
cdk deploy
```

### 7. Tips Para el despliegue


El despliegue lo utiliza utilizando las credenciales por defecto de AWS, si desea usar un profile espec铆fico agregue --profile <nombre> al comando deploy:

```
cdk deploy --profile mi-profile-custom
```

o simplemente exporte en una variable de entorno

```
export AWS_PROFILE=mi-profile-custom
cdk deploy
```

### 8. La aplicaci贸n

Cuando realices el despliegue te llegara un correo solicitando confirmaci贸n para la suscripci贸n del SNS, el correo es como este: 

![confirmacion](imagen/confirmacion.jpeg)

Y cuando aceptes debes ver el siguiente mensaje: 

![aceptado](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/g1y7zh7soel5uow4s7ol.jpeg)

Esto es importante porque, ya que de lo contrario no recibir谩s el e-mail.

Para iniciar la aplicaci贸n debes identificar el bucket S3 en el Stack de cloudformation, el nombre del bucket debe ser algo como: 

```
s3://scan-video-s3-rekognition-databucketxxxxxxxxxx
```

Accede al bucket y carga el video, recuerda que debe ser en formato .mp4

![bucket](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/0a65fo8ocxo54ksz2o5u.jpeg)

Cuando cargues el archivo de video las lambdas se empezaran a ejecutar, esto puede tardar unos minutos mientras lo puedes monitorear en Amazon CloudWatch. 

Una vez finalizada la revisi贸n podr谩s ser capaz de ver las etiquetas del video en Dynamodb:

![Dynamodb](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/mcw70x22a4roccujbtbg.jpeg)

Y cada Item debe tener la siguiente estructura: 

![Item](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/njp5abntpil009podoof.jpeg)

Con esta data en DynamoDB puedes hacer dashboard en [Amazon Quicksight](https://aws.amazon.com/es/quicksight/), hacer ETL con [AWS Glue](https://aws.amazon.com/es/quicksight/)... en realidad todo lo que te ocurra. 馃殌馃殌馃殌 


### 9. Eliminar el stack de la aplicaci贸n

Esta aplicaci贸n no elimina el bucket si contiene videos, por lo que primero debes vaciar el bucket y luego proceder a destruir el stak. 


Para eliminar el stack lo puedes hacer via comando:

```
cdk destroy
```

贸 via consola cloudformation, seleccione el stack (mismo nombre del proyecto cdk) y lo borra.

## 隆隆Happy developing 馃榿!!

----

## Adicional

* Te dejo este proyecto m谩s grande que te puede interesar 

https://github.com/aws-samples/amazon-rekognition-serverless-large-scale-image-and-video-processing

* Una soluci贸n que puedes agregar al princio que convierta el video previamente a formato mp4

[AWS Elemental MediaConvert](https://aws.amazon.com/es/mediaconvert/)

* La arquitectura original

https://aws.amazon.com/es/blogs/machine-learning/scan-amazon-s3-buckets-for-content-moderation-using-s3-batch-and-amazon-rekognition/

___

## Servicios involucrados en la soluci贸n son

### Amazon S3 (Simple Storage Service):
[S3](https://aws.amazon.com/es/s3/) es un servicio de computo sin servidor que le permite ejecutar c贸digo sin aprovisionar ni administrar servidores.

### Amazon Rekognition Video:
[Amazon Rekognition Video](https://aws.amazon.com/es/rekognition/video-features/) 
Amazon Rekognition le permite analizar im谩genes y videos autom谩ticamente en sus aplicaciones y contenido. Proporciona una imagen o un video a la API de Amazon Rekognition, y el servicio puede identificar los objetos, las personas, el texto, las escenas y las actividades, adem谩s de detectar cualquier contenido inapropiado.

Amazon Rekognition Video es un servicio de an谩lisis de videos con tecnolog铆a de aprendizaje autom谩tico que detecta objetos, escenas, celebridades, texto, actividades y cualquier contenido inapropiado en los videos almacenados en Amazon S3. Rekognition Video tambi茅n proporciona un an谩lisis de rostros muy preciso y funciones de b煤squeda de rostros para detectarlos, analizarlos y compararlos; y ayuda a comprender el movimiento de las personas en los videos.

### AWS Lamdba: 
AWS [Lambda](https://aws.amazon.com/es/lambda/) es un servicio de computo sin servidor que le permite ejecutar c贸digo sin aprovisionar ni administrar servidores. 

### Amazon DynamoDB:
Amazon [DynamoDB](https://docs.aws.amazon.com/es_es/amazondynamodb/latest/developerguide/Introduction.html) es un servicio de base de datos de NoSQL completamente administrado que ofrece un desempe帽o r谩pido y predecible, as铆 como una escalabilidad 贸ptima. DynamoDB le permite reducir las cargas administrativas que supone tener que utilizar y escalar una base de datos distribuida, lo que le evita tener que preocuparse por el aprovisionamiento del hardware, la configuraci贸n y la configuraci贸n, la replicaci贸n, los parches de software o el escalado de cl煤steres.

### Amazon Simple Notification Service (SNS)
[SNS](https://aws.amazon.com/es/sns/?whats-new-cards.sort-by=item.additionalFields.postDateTime&whats-new-cards.sort-order=desc) es un servicio de mensajer铆a completamente administrado para la comunicaci贸n aplicaci贸n a aplicaci贸n (A2A) y aplicaci贸n a persona (A2P).

La funcionalidad de publicaci贸n/suscripci贸n A2A brinda temas para la mensajer铆a de alto rendimiento, de muchos a muchos, basada en push entre sistemas distribuidos, microservicios y aplicaciones sin servidores controladas por eventos. Mediante el uso de temas de Amazon SNS, los sistemas de publicadores pueden distribuir los mensajes a una gran cantidad de sistemas de suscriptores, entre otros, colas de Amazon SQS, funciones de AWS Lambda y puntos de enlace HTTPS, para procesamiento paralelo y Amazon Kinesis Data Firehose. La funcionalidad A2P permite enviar mensajes a usuarios a escala a trav茅s de SMS, push m贸vil e email.

### CDK (Cloud Development Kit): 
El kit de desarrollo de la nube de AWS (AWS CDK) es un framework de c贸digo abierto que sirve para definir los recursos destinados a aplicaciones en la nube mediante lenguajes de programaci贸n conocidos.

Una vez lo conozcas... no vas a querer desarrollar aplicaciones en AWS de otra forma ;)

Conoce m谩s ac谩: [CDK](https://aws.amazon.com/es/cdk/?nc1=h_ls)

---


##隆Gracias!

Te dejo mis redes para que me sigas: 
[Dev.to](https://dev.to/elizabethfuentes12)
[Linkedin](https://www.linkedin.com/in/lizfue/)