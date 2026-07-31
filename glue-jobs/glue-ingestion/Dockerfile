# Dockerfile for local development and testing of AWS Glue job
# This multi-stage build creates a self-contained environment for running the Glue job locally

# STAGE 1: Build the package
# Using the official AWS Glue base image as our foundation
FROM public.ecr.aws/glue/aws-glue-libs:glue_libs_4.0.0_image_01 AS base

# Switch to root to fix permissions and line endings
USER root

# Fix Python symlink - make 'python' point to 'python3' instead of 'python2'
# This is needed because Poetry 1.8.0 uses 'python -I' flag which doesn't exist in Python 2.7
RUN ln -sf /usr/local/bin/python3 /usr/bin/python

# Install Poetry for package management
RUN --mount=type=cache,target=/root/.cache/pip \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install poetry==1.8.0 --prefix=/usr/local && \
    ln -s /usr/local/bin/poetry /usr/bin/poetry

WORKDIR /app

# Copy glue-core files (build context is root directory)
COPY glue-jobs/glue-core /app/glue-jobs/glue-core

# Copy glue-ingestion files
COPY glue-jobs/glue-ingestion/ingestion /app/glue-jobs/glue-ingestion/ingestion
COPY glue-jobs/glue-ingestion/glue_job.py /app/glue-jobs/glue-ingestion/glue_job.py
COPY glue-jobs/glue-ingestion/pyproject.toml /app/glue-jobs/glue-ingestion/pyproject.toml
COPY glue-jobs/glue-ingestion/poetry.lock /app/glue-jobs/glue-ingestion/poetry.lock
COPY glue-jobs/glue-ingestion/README.md /app/glue-jobs/glue-ingestion/README.md

# Copy the build script and ensure it has Unix line endings and is executable
COPY ci/scripts/build-glue-ingestion.sh /app/ci/scripts/build-glue-ingestion.sh

# Fix line endings and make executable
RUN sed -i 's/\r$//' /app/ci/scripts/build-glue-ingestion.sh && \
    chmod +x /app/ci/scripts/build-glue-ingestion.sh

# Build the package using the script
RUN bash /app/ci/scripts/build-glue-ingestion.sh

# STAGE 2: Create the final image for running the Glue job
# This stage creates a runtime environment for the Glue job
FROM public.ecr.aws/glue/aws-glue-libs:glue_libs_4.0.0_image_01

# Install pip (needed for wheel installation)
RUN python3 -m ensurepip --upgrade

# Set the working directory
WORKDIR /app

# Copy the Glue job script and the built wheels from the base image / STAGE 1
COPY --from=base /app/glue-jobs/glue-ingestion/glue_job.py /app/glue-jobs/glue-ingestion/glue_job.py
COPY --from=base /app/glue-jobs/glue-ingestion/dist/ /app/glue-jobs/glue-ingestion/dist/
# Copy glue-core source for path dependency resolution
COPY --from=base /app/glue-jobs/glue-core /app/glue-jobs/glue-core
# Copy config files for local development
COPY --from=base /app/glue-jobs/glue-ingestion/ingestion/envs /app/glue-jobs/glue-ingestion/ingestion/envs

# Install both wheel packages (glue-core first, then ingestion)
RUN python3 -m pip install /app/glue-jobs/glue-ingestion/dist/glue_core-*.whl && \
    python3 -m pip install /app/glue-jobs/glue-ingestion/dist/ingestion-*.whl

# Add the unzipped libraries to the Python path
# This ensures that Glue libraries are available to our application
ENV PYTHONPATH=/app:/home/glue_user/aws-glue-libs/PyGlue.zip:/home/glue_user/spark/python/lib/pyspark.zip

# Set proper ENTRYPOINT and CMD
# This makes the container executable directly with our Glue job script
ENTRYPOINT ["/usr/local/bin/python3"]
CMD ["/app/glue-jobs/glue-ingestion/glue_job.py", "--JOB_NAME", "local-ingestion-job", "--ENVIRONMENT", "dev"]
