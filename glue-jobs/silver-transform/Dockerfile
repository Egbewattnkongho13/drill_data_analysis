# Dockerfile for local development and testing of AWS Glue silver-transform job
# Pre-requisite: Build wheels locally using: make build-wheel

FROM public.ecr.aws/glue/aws-glue-libs:glue_libs_4.0.0_image_01 AS base

# Switch to root for installations
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

# Copy silver-transform files
COPY glue-jobs/silver-transform/ingestion /app/glue-jobs/silver-transform/ingestion
COPY glue-jobs/silver-transform/threed_w_transform_job.py /app/glue-jobs/silver-transform/threed_w_transform_job.py
COPY glue-jobs/silver-transform/pyproject.toml /app/glue-jobs/silver-transform/pyproject.toml
COPY glue-jobs/silver-transform/README.md /app/glue-jobs/silver-transform/README.md

# Copy the build script and ensure it has Unix line endings and is executable
COPY ci/scripts/build-silver-transform.sh /app/ci/scripts/build-silver-transform.sh

# Fix line endings and make executable
RUN sed -i 's/\r$//' /app/ci/scripts/build-silver-transform.sh && \
    chmod +x /app/ci/scripts/build-silver-transform.sh

# Build the package using the script
RUN bash /app/ci/scripts/build-silver-transform.sh

# STAGE 2: Create the final image for running the Glue job
# This stage creates a runtime environment for the Glue job
FROM public.ecr.aws/glue/aws-glue-libs:glue_libs_4.0.0_image_01

# Switch to root for installations
USER root

# Install pip (needed for wheel installation)
RUN python3 -m ensurepip --upgrade

# Set the working directory
WORKDIR /app

# Copy the Glue job script and the built wheels from the base image / STAGE 1
COPY --from=base /app/glue-jobs/silver-transform/threed_w_transform_job.py /app/glue-jobs/silver-transform/threed_w_transform_job.py
COPY --from=base /app/glue-jobs/silver-transform/dist/ /app/glue-jobs/silver-transform/dist/
# Copy glue-core source for path dependency resolution
COPY --from=base /app/glue-jobs/glue-core /app/glue-jobs/glue-core

# Install both wheel packages (glue-core first, then silver-transform)
RUN python3 -m pip install /app/glue-jobs/silver-transform/dist/glue_core-*.whl && \
    python3 -m pip install /app/glue-jobs/silver-transform/dist/silver_transform-*.whl

# Add the unzipped libraries to the Python path
# This ensures that Glue libraries are available to our application
ENV PYTHONPATH=/app:/home/glue_user/aws-glue-libs/PyGlue.zip:/home/glue_user/spark/python/lib/pyspark.zip

# Set proper ENTRYPOINT and CMD
# This makes the container executable directly with our Glue job script
ENTRYPOINT ["/usr/local/bin/python3"]
CMD ["/app/glue-jobs/silver-transform/threed_w_transform_job.py", "--JOB_NAME", "local-silver-transform-job", "--ENVIRONMENT", "dev"]
