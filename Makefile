version ?= 0.5.0
image_name ?= mesosphere/marathon-autoscaler
full_image_name ?= $(image_name):v$(version)

.PHONY: certs base clean gen-universe

build:
	docker build -t $(full_image_name) .

push:
	docker push $(full_image_name)

clean:
	docker rmi $(full_image_name)
