# Use AWS Lambda Python 3.9 base image
FROM public.ecr.aws/lambda/python:3.9

# Install system dependencies for pyzbar
RUN yum install -y zbar zbar-devel && yum clean all

# Copy requirements and install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ ${LAMBDA_TASK_ROOT}/api/
COPY debtorportal/ ${LAMBDA_TASK_ROOT}/debtorportal/
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/
COPY pdf_worker.py ${LAMBDA_TASK_ROOT}/
COPY manage.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD [ "lambda_handler.handler" ]
