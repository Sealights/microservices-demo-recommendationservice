docker build -t recommendationservice .
docker tag recommendationservice:latest 159616352881.dkr.ecr.eu-west-1.amazonaws.com/microservices-demo-recommendationservice:latest
docker push 159616352881.dkr.ecr.eu-west-1.amazonaws.com/microservices-demo-recommendationservice:latest
