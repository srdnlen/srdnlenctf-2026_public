docker build -t compile_linx -f Dockerfile.compile .
mkdir -p build
docker run --rm -t -v $(pwd)/build:/app/build compile_linx
