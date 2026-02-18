# Dockerfile for local development and testing of AWS Glue job
# This multi-stage build creates a self-contained environment for running the Glue job locally

# STAGE 1: Build the package
# Using the official AWS Glue base image as our foundation
FROM public.ecr.aws/glue/aws-glue-libs:glue_libs_4.0.0_image_01 AS base

# Switch to root to fix permissions and line endings
USER root

# Install Poetry for package management
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install poetry==1.8.0 --prefix=/usr/local && \
    ln -s /usr/local/bin/poetry /usr/bin/poetry

# Copy glue files (build context is root directory)
# This copies all necessary files for building the package
COPY glue/ingestion /app/glue/ingestion
COPY glue/glue_job.py /app/glue/glue_job.py
COPY glue/pyproject.toml /app/glue/pyproject.toml
COPY glue/poetry.lock /app/glue/poetry.lock
COPY glue/README.md /app/glue/README.md

# Copy the build script and ensure it has Unix line endings and is executable
COPY ci/scripts/build-glue-package.sh /app/ci/scripts/build-glue-package.sh

# Fix line endings and make executable
RUN sed -i 's/\r$//' /app/ci/scripts/build-glue-package.sh && \
    chmod +x /app/ci/scripts/build-glue-package.sh

# Build the package using the script
WORKDIR /app/glue
RUN bash /app/ci/scripts/build-glue-package.sh

# STAGE 2: Create the final image for running the Glue job
# This stage creates a runtime environment for the Glue job
FROM public.ecr.aws/glue/aws-glue-libs:glue_libs_4.0.0_image_01

# Install pip (needed for wheel installation)
RUN python3 -m ensurepip --upgrade

# Set the working directory
WORKDIR /app

# Copy the Glue job script and the built wheel from the base image / STAGE 1
COPY --from=base /app/glue/glue_job.py /app/glue/glue_job.py
COPY --from=base /app/glue/dist/ /app/glue/dist/

# Install the wheel package that contains our ingestion logic
RUN python3 -m pip install /app/glue/dist/glue_ingestion-*.whl

# Add the unzipped libraries to the Python path
# This ensures that Glue libraries are available to our application
ENV PYTHONPATH=/app:/home/glue_user/aws-glue-libs/PyGlue.zip:/home/glue_user/spark/python/lib/pyspark.zip

# Set proper ENTRYPOINT and CMD
# This makes the container executable directly with our Glue job script
ENTRYPOINT ["/usr/local/bin/python3"]
CMD ["/app/glue/glue_job.py", "--JOB_NAME", "local-ingestion-job", "--ENVIRONMENT", "dev"]
