from rest_framework import serializers

from vendor.models import HistoricalPerformance
from vendor.serializers import VendorSerializer


class HistoricalPerformanceSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)

    class Meta:
        model = HistoricalPerformance
        fields = "__all__"
        read_only_fields = (
            "external_id",
            "vendor",
            "date",
            "on_time_delivery_rate",
            "quality_rating_avg",
            "avg_response_time",
            "fulfillment_rate",
        )
