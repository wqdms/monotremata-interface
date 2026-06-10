

{% autoescape off %}
class {{ className }}ModelViewSet({{ viewsetClassParent }}):
    serializer_class = serializers.{{className}}ModelSerializer
    queryset = serializer_class.Meta.model.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
{% endautoescape %}
