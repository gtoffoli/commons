from channels.routing import route

channel_routing = [
    route("http.request", "commons.consumers.http_consumer"),
]
