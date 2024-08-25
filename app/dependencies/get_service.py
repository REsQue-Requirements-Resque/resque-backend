from typing import Any, Type, Dict
from .get_repository import get_repository

Service = Type[Any]


class ServiceFactory:
    def __init__(self):
        self.service_instances: Dict[Type[Service], Service] = {}

    def get_service(self, service_class: Type[Service]) -> Service:
        if not hasattr(service_class, "repository"):
            raise NotImplementedError(
                "The service class must have a 'repository' attribute"
            )

        if service_class not in self.service_instances:
            repository = get_repository(service_class.repository)
            self.service_instances[service_class] = service_class(repository)
        return self.service_instances[service_class]


service_factory = ServiceFactory()
get_service = service_factory.get_service
