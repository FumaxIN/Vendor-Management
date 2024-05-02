from datetime import datetime

from django.utils import timezone
from celery import shared_task

from vendor.models import PurchaseOrder, HistoricalPerformance


@shared_task
def calculate_avg_response_time(po_id):
    po = PurchaseOrder.objects.get(po_number=po_id)
    vendor = po.vendor
    tot_acknowledged_pos = vendor.cache_data["tot_acknowledged_pos"]
    po_response_time = po.acknowledgment_date - po.issue_date
    po_response_time_minutes = po_response_time.seconds / 60
    vendor.avg_response_time = (
                                       (vendor.avg_response_time * tot_acknowledged_pos) + po_response_time_minutes
                               ) / (tot_acknowledged_pos + 1)

    vendor.cache_data["tot_acknowledged_pos"] += 1

    vendor.save()


@shared_task
def calculate_performance_metrics(po_id):
    po = PurchaseOrder.objects.get(po_number=po_id)
    vendor = po.vendor
    tot_on_time_deliveries = vendor.cache_data["tot_on_time_deliveries"]
    tot_completed_pos = vendor.cache_data["tot_completed_pos"]
    if po.delivery_date <= timezone.now():
        tot_on_time_deliveries += 1
    vendor.on_time_delivery_rate = tot_on_time_deliveries / (tot_completed_pos + 1)
    vendor.fulfillment_rate = (tot_completed_pos + 1) / vendor.cache_data["tot_pos"]
    vendor.quality_rating_avg = (
                                          (vendor.quality_rating_avg * tot_completed_pos) + po.quality_rating
                                 ) / (tot_completed_pos + 1)

    vendor.cache_data["tot_completed_pos"] += 1
    vendor.cache_data["tot_on_time_deliveries"] = tot_on_time_deliveries

    vendor.save()


@shared_task
def calculate_historical_performance_metrics(vendor):
    pos = PurchaseOrder.objects.filter(vendor=vendor)
    if not pos.exists():
        return

    on_time_delivery_rate = 0
    quality_rating_avg = 0
    fulfillment_rate = 0
    total_pos = pos.count()
    total_delivered_on_time = 0
    total_fulfilled = 0
    total_quality_rating = 0
    for po in pos:
        if po.status == "completed":
            total_fulfilled += 1
            if po.delivery_date <= po.acknowledgment_date:
                total_delivered_on_time += 1
            total_quality_rating += po.quality_rating

    try:
        on_time_delivery_rate = (total_delivered_on_time / total_fulfilled) * 100
    except ZeroDivisionError:
        on_time_delivery_rate = 0

    try:
        quality_rating_avg = total_quality_rating / total_fulfilled
    except ZeroDivisionError:
        quality_rating_avg = 0

    try:
        fulfillment_rate = (total_fulfilled / total_pos) * 100
    except ZeroDivisionError:
        fulfillment_rate = 0

    HistoricalPerformance.objects.create(
        vendor=vendor,
        date=datetime.now().date(),
        on_time_delivery_rate=on_time_delivery_rate,
        quality_rating_avg=quality_rating_avg,
        avg_response_time=vendor.avg_response_time,
        fulfillment_rate=fulfillment_rate,
    )
